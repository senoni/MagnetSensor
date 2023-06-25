const int ADC_PIN = A0;

void setup() {
  // Start the serial communication
  Serial.begin(250000);

  // Configure ADC
  analogReadResolution(12); // Set ADC resolution to 12 bits (0-4095)
  analogSetPinAttenuation(ADC_PIN, ADC_11db);
}

void loop() {
  // Read ADC value
  int adcValue = analogRead(ADC_PIN);

  // Send ADC value over serial
  Serial.println(adcValue);

  delayMicroseconds(1);
}