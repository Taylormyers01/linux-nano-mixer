
const int NUM_SLIDERS = 7;

int sliderPins[NUM_SLIDERS] = {A0, A1, A2, A3, A4, A5, A6};

int lastValues[NUM_SLIDERS];

void setup() {
  Serial.begin(115200);

  for (int i = 0; i < NUM_SLIDERS; i++) {
    lastValues[i] = -1;
  }
}

void loop() {

  for (int i = 0; i < NUM_SLIDERS; i++) {

    int value = analogRead(sliderPins[i]);

    // only send if changed enough
    if (abs(value - lastValues[i]) > 4) {

      Serial.print(i);
      Serial.print(":");
      Serial.println(value);

      lastValues[i] = value;
    }
  }

  delay(10);
}