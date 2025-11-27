// Arduino Uno -> DM542 - DIAGNOSTIC VERSION
const int PUL_PIN = 2;      // Step
const int DIR_PIN = 3;      // Direction
const int LIMIT_SW_PIN = 8; // Limit switch (pulled to GND when valve fully closed)

// motion parameters
const long STEPS_PER_MOVE = 125;
const int STEP_DELAY_US   = 125;        // Fast speed for normal operation
const int HOMING_DELAY_US = 500;        // Medium speed for initial homing
const int SLOW_HOMING_DELAY_US = 1000;  // Slow speed for final approach
const int BACKUP_STEPS = 500;           // Quarter turn backup (2000 steps/rev)
const int STEPS_PER_REV = 2000;         // Steps per revolution
const int HOMING_TIMEOUT_STEPS = 10000; // Max steps before homing timeout
const float MAX_OPEN_TURNS = 3.0;       // Maximum turns allowed in open direction

// Position tracking
volatile long currentPosition = 0;      // Steps from home (0 = fully closed)
const long MAX_OPEN_POSITION = (long)(MAX_OPEN_TURNS * STEPS_PER_REV);  // Max allowed position
const int CLOSING_DIR = LOW;            // DIR=LOW closes the valve
const int OPENING_DIR = HIGH;           // DIR=HIGH opens the valve

void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(PUL_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  pinMode(LIMIT_SW_PIN, INPUT_PULLUP);  // Use internal pullup, switch pulls to GND

  digitalWrite(PUL_PIN, LOW);
  digitalWrite(DIR_PIN, LOW);

  blinkReady();
  
  // HOMING SEQUENCE
  Serial.println("=== HOMING SEQUENCE ===");
  performHoming();
  
  Serial.println("=== HOMING COMPLETE ===");
  Serial.println("READY - Send 'r' (open) or 'l' (close)");
}

void loop() {
  // Check if limit switch is pressed and update home position
  if (digitalRead(LIMIT_SW_PIN) == LOW) {
    if (currentPosition != 0) {
      Serial.print("Limit switch triggered! Updating home position. Was: ");
      Serial.print(currentPosition);
      Serial.println(" steps from home");
      currentPosition = 0;  // Reset to home position
    }
  }
  
  if (Serial.available() > 0) {
    char c = Serial.read();

    if (c == 'r' || c == 'R') {
      digitalWrite(LED_BUILTIN, HIGH);
      Serial.println("\n>>> Command 'r' received - Opening valve (DIR=HIGH)");
      
      // Check if at maximum open position
      if (currentPosition >= MAX_OPEN_POSITION) {
        Serial.print(">>> Already at maximum open position (");
        Serial.print(MAX_OPEN_TURNS);
        Serial.println(" turns)! Cannot open further.");
        Serial.println(">>> Done");
        return;
      }
      
      digitalWrite(DIR_PIN, OPENING_DIR);
      delay(50);
      
      // Move towards open position, but stop if max position reached
      for(int i=0; i<100; i++) {
        if (currentPosition >= MAX_OPEN_POSITION) {
          Serial.println(">>> Maximum open position reached during opening!");
          break;
        }
        digitalWrite(PUL_PIN, HIGH);
        delayMicroseconds(STEP_DELAY_US);
        digitalWrite(PUL_PIN, LOW);
        delayMicroseconds(STEP_DELAY_US);
        currentPosition++;  // Moving away from home
      }
      delay(500);
      Serial.print(">>> Done. Position: ");
      Serial.print(currentPosition);
      Serial.print(" steps from home (");
      Serial.print((float)currentPosition / STEPS_PER_REV, 2);
      Serial.println(" turns)");
    }

    if (c == 'l' || c == 'L') {
      digitalWrite(LED_BUILTIN, LOW);
      Serial.println("\n>>> Command 'l' received - Closing valve (DIR=LOW)");
      
      // Check if already at limit before moving
      if (digitalRead(LIMIT_SW_PIN) == LOW) {
        Serial.println(">>> Already at limit switch! Cannot close further.");
        Serial.println(">>> Done");
        return;
      }
      
      digitalWrite(DIR_PIN, CLOSING_DIR);
      delay(50);
      
      // Move towards closed position, but stop if limit switch is hit
      for(int i=0; i<100; i++) {
        if (digitalRead(LIMIT_SW_PIN) == LOW) {
          Serial.println(">>> Limit switch reached during closing!");
          currentPosition = 0;
          break;
        }
        digitalWrite(PUL_PIN, HIGH);
        delayMicroseconds(STEP_DELAY_US);
        digitalWrite(PUL_PIN, LOW);
        delayMicroseconds(STEP_DELAY_US);
        currentPosition--;  // Moving towards home
        if (currentPosition < 0) currentPosition = 0;  // Don't go negative
      }
      delay(500);
      Serial.print(">>> Done. Position: ");
      Serial.print(currentPosition);
      Serial.print(" steps from home (");
      Serial.print((float)currentPosition / STEPS_PER_REV, 2);
      Serial.println(" turns)");
    }
  }
}

void blinkReady() {
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(150);
    digitalWrite(LED_BUILTIN, LOW);
    delay(150);
  }
}

void performHoming() {
  Serial.println("Starting homing routine...");
  
  // Check if already at limit switch
  if (digitalRead(LIMIT_SW_PIN) == LOW) {
    Serial.println("Already at limit switch. Backing off...");
    // Back off from limit switch
    digitalWrite(DIR_PIN, OPENING_DIR);
    delay(50);
    for(int i=0; i<BACKUP_STEPS; i++) {
      digitalWrite(PUL_PIN, HIGH);
      delayMicroseconds(HOMING_DELAY_US);
      digitalWrite(PUL_PIN, LOW);
      delayMicroseconds(HOMING_DELAY_US);
    }
    delay(200);
  }
  
  // FIRST APPROACH - Medium speed until limit switch is hit
  Serial.println("Phase 1: Moving to limit switch at medium speed...");
  digitalWrite(DIR_PIN, CLOSING_DIR);  // Close valve (DIR=LOW)
  delay(50);
  
  int stepCount = 0;
  while (digitalRead(LIMIT_SW_PIN) == HIGH) {  // HIGH = not pressed (pullup)
    digitalWrite(PUL_PIN, HIGH);
    delayMicroseconds(HOMING_DELAY_US);
    digitalWrite(PUL_PIN, LOW);
    delayMicroseconds(HOMING_DELAY_US);
    stepCount++;
    
    // Safety timeout - prevent infinite loop
    if (stepCount > HOMING_TIMEOUT_STEPS) {
      Serial.print("ERROR: Limit switch not found after ");
      Serial.print(HOMING_TIMEOUT_STEPS);
      Serial.println(" steps!");
      Serial.println("Homing FAILED - Please check limit switch wiring");
      return;
    }
  }
  Serial.println("Limit switch contacted!");
  delay(200);
  
  // BACKUP - Move away from limit switch
  Serial.print("Phase 2: Backing up ");
  Serial.print(BACKUP_STEPS);
  Serial.println(" steps...");
  digitalWrite(DIR_PIN, OPENING_DIR);
  delay(50);
  for(int i=0; i<BACKUP_STEPS; i++) {
    digitalWrite(PUL_PIN, HIGH);
    delayMicroseconds(HOMING_DELAY_US);
    digitalWrite(PUL_PIN, LOW);
    delayMicroseconds(HOMING_DELAY_US);
  }
  delay(200);
  
  // FINAL APPROACH - Slow speed for precise homing
  Serial.println("Phase 3: Final approach at slow speed...");
  digitalWrite(DIR_PIN, CLOSING_DIR);
  delay(50);
  
  while (digitalRead(LIMIT_SW_PIN) == HIGH) {
    digitalWrite(PUL_PIN, HIGH);
    delayMicroseconds(SLOW_HOMING_DELAY_US);
    digitalWrite(PUL_PIN, LOW);
    delayMicroseconds(SLOW_HOMING_DELAY_US);
  }
  
  Serial.println("Homing complete - Limit switch verified!");
  currentPosition = 0;  // Set home position
  Serial.println("Position set to 0 (fully closed)");
}