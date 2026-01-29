/*
  Uno R4 WiFi + DM542 valve controller over USB Serial (USB-C)

  - Serial input:
      'r' / 'R' => open valve (100 steps)
      'l' / 'L' => close valve (100 steps)

  Safety:
  - Homes on startup toward close until limit switch triggers -> position = 0
  - Enforces max open travel (MAX_OPEN_TURNS)
  - Never drives further closed once limit switch is hit (resets position to 0)
*/

#include <Arduino.h>

// ---------- Valve I/O ----------
const int PUL_PIN      = 2;   // Step
const int DIR_PIN      = 3;   // Direction
const int LIMIT_SW_PIN = 8;   // Limit switch (pulled to GND when fully closed)

// motion parameters
const int  STEP_DELAY_US        = 125;   // normal speed
const int  HOMING_DELAY_US      = 500;   // homing speed
const int  SLOW_HOMING_DELAY_US = 1000;  // final homing approach
const int  BACKUP_STEPS         = 500;   // quarter turn backup (at 2000 steps/rev)
const int  STEPS_PER_REV        = 2000;  // per your setup
const int  HOMING_TIMEOUT_STEPS = 10000; // safety

const float MAX_OPEN_TURNS = 1.0; // allowed open travel
volatile long currentPosition = 0; // steps from home (0 = fully closed)
const long MAX_OPEN_POSITION = (long)(MAX_OPEN_TURNS * STEPS_PER_REV);

const int CLOSING_DIR = LOW;   // DIR=LOW closes the valve
const int OPENING_DIR = HIGH;  // DIR=HIGH opens the valve

// ---------- Command handling ----------
enum Cmd { CMD_NONE, CMD_OPEN, CMD_CLOSE };
volatile Cmd pendingCmd = CMD_NONE;
bool busy = false;

// ---------- Motion helpers ----------
inline void stepOnce(int delayUs) {
  digitalWrite(PUL_PIN, HIGH);
  delayMicroseconds(delayUs);
  digitalWrite(PUL_PIN, LOW);
  delayMicroseconds(delayUs);
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
  Serial.println("=== HOMING SEQUENCE ===");
  Serial.println("Starting homing routine...");

  // If already at limit, back off first
  if (digitalRead(LIMIT_SW_PIN) == LOW) {
    Serial.println("Already at limit switch. Backing off...");
    digitalWrite(DIR_PIN, OPENING_DIR);
    delay(50);
    for (int i = 0; i < BACKUP_STEPS; i++) {
      stepOnce(HOMING_DELAY_US);
    }
    delay(200);
  }

  // Phase 1: approach at medium speed until limit hits (or timeout)
  Serial.println("Phase 1: Moving to limit switch at medium speed...");
  digitalWrite(DIR_PIN, CLOSING_DIR);
  delay(50);

  int stepCount = 0;
  while (digitalRead(LIMIT_SW_PIN) == HIGH) {
    stepOnce(HOMING_DELAY_US);
    stepCount++;

    if (stepCount > HOMING_TIMEOUT_STEPS) {
      Serial.print("ERROR: Limit switch not found after ");
      Serial.print(HOMING_TIMEOUT_STEPS);
      Serial.println(" steps!");
      Serial.println("Homing FAILED - Check limit switch wiring");
      return;
    }
  }
  Serial.println("Limit switch contacted!");
  delay(200);

  // Phase 2: back up
  Serial.print("Phase 2: Backing up ");
  Serial.print(BACKUP_STEPS);
  Serial.println(" steps...");
  digitalWrite(DIR_PIN, OPENING_DIR);
  delay(50);
  for (int i = 0; i < BACKUP_STEPS; i++) {
    stepOnce(HOMING_DELAY_US);
  }
  delay(200);

  // Phase 3: final slow approach
  Serial.println("Phase 3: Final approach at slow speed...");
  digitalWrite(DIR_PIN, CLOSING_DIR);
  delay(50);

  int slowCount = 0;
  while (digitalRead(LIMIT_SW_PIN) == HIGH) {
    stepOnce(SLOW_HOMING_DELAY_US);
    slowCount++;
    if (slowCount > HOMING_TIMEOUT_STEPS) {
      Serial.println("ERROR: Timeout during slow homing approach!");
      return;
    }
  }

  Serial.println("Homing complete - Limit switch verified!");
  currentPosition = 0;
  Serial.println("Position set to 0 (fully closed)");
  Serial.println("=== HOMING COMPLETE ===");
}

// one "command move" (100 steps per command)
void doOpenCommand() {
  digitalWrite(LED_BUILTIN, HIGH);
  Serial.println(">>> OPEN command (DIR=HIGH)");

  if (currentPosition >= MAX_OPEN_POSITION) {
    Serial.print(">>> At max open position (");
    Serial.print(MAX_OPEN_TURNS);
    Serial.println(" turns). Ignoring.");
    return;
  }

  digitalWrite(DIR_PIN, OPENING_DIR);
  delay(50);

  for (int i = 0; i < 100; i++) {
    if (currentPosition >= MAX_OPEN_POSITION) {
      Serial.println(">>> Max open reached during opening.");
      break;
    }
    stepOnce(STEP_DELAY_US);
    currentPosition++;
  }

  Serial.print(">>> Done. Position: ");
  Serial.print(currentPosition);
  Serial.print(" steps (");
  Serial.print((float)currentPosition / STEPS_PER_REV, 2);
  Serial.println(" turns)");
}

void doCloseCommand() {
  digitalWrite(LED_BUILTIN, LOW);
  Serial.println(">>> CLOSE command (DIR=LOW)");

  if (digitalRead(LIMIT_SW_PIN) == LOW) {
    Serial.println(">>> Already at limit switch. Ignoring.");
    currentPosition = 0;
    return;
  }

  digitalWrite(DIR_PIN, CLOSING_DIR);
  delay(50);

  for (int i = 0; i < 100; i++) {
    if (digitalRead(LIMIT_SW_PIN) == LOW) {
      Serial.println(">>> Limit switch reached during closing!");
      currentPosition = 0;
      break;
    }
    stepOnce(STEP_DELAY_US);
    if (currentPosition > 0) currentPosition--;
    else currentPosition = 0;
  }

  Serial.print(">>> Done. Position: ");
  Serial.print(currentPosition);
  Serial.print(" steps (");
  Serial.print((float)currentPosition / STEPS_PER_REV, 2);
  Serial.println(" turns)");
}

void setup() {
  Serial.begin(115200);
  while (!Serial) {}

  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(PUL_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  pinMode(LIMIT_SW_PIN, INPUT_PULLUP);

  digitalWrite(PUL_PIN, LOW);
  digitalWrite(DIR_PIN, LOW);

  blinkReady();

  // Home first (no reliance on networking)
  performHoming();

  Serial.println("READY");
  Serial.println(" - Serial: send 'r' (open) or 'l' (close)");
}

// Read one meaningful command char from serial, ignoring whitespace/newlines.
// Returns CMD_NONE if nothing useful was read.
Cmd readSerialCmd() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();

    // ignore common line endings / whitespace
    if (c == '\n' || c == '\r' || c == ' ' || c == '\t') continue;

    if (c == 'r' || c == 'R') return CMD_OPEN;
    if (c == 'l' || c == 'L') return CMD_CLOSE;

    // unknown char: ignore, but print for debugging
    Serial.print("[serial] ignored char: 0x");
    Serial.println((unsigned char)c, HEX);
  }
  return CMD_NONE;
}

void loop() {
  // Update home if limit switch hits unexpectedly
  if (digitalRead(LIMIT_SW_PIN) == LOW && currentPosition != 0) {
    Serial.print("Limit switch triggered! Position was ");
    Serial.print(currentPosition);
    Serial.println(" steps. Resetting to 0.");
    currentPosition = 0;
  }

  // Serial command -> pendingCmd
  Cmd c = readSerialCmd();
  if (c != CMD_NONE) pendingCmd = c;

  // Execute pending command (one at a time)
  if (!busy && pendingCmd != CMD_NONE) {
    busy = true;
    Cmd cmd = pendingCmd;
    pendingCmd = CMD_NONE;

    if (cmd == CMD_OPEN)  doOpenCommand();
    if (cmd == CMD_CLOSE) doCloseCommand();

    busy = false;
  }

  delay(5);
}
