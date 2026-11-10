namespace ScanSample;

public static class TemperatureConverter
{
    public static decimal CelsiusToFahrenheit(decimal celsius)
    {
        if (celsius < -273.15m)
        {
            throw new ArgumentOutOfRangeException(nameof(celsius), "Temperature cannot be below absolute zero.");
        }

        return celsius * 9 / 5 + 32;
    }
}
