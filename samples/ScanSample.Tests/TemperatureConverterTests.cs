using System.Globalization;
using Xunit;

namespace ScanSample.Tests;

public class TemperatureConverterTests
{
    [Theory]
    [InlineData("-273.15", "-459.67")]
    [InlineData("-40", "-40")]
    [InlineData("0", "32")]
    [InlineData("100", "212")]
    public void ConvertsTemperaturesAtAndAboveAbsoluteZero(string celsius, string expected)
    {
        Assert.Equal(decimal.Parse(expected, CultureInfo.InvariantCulture),
            TemperatureConverter.CelsiusToFahrenheit(decimal.Parse(celsius, CultureInfo.InvariantCulture)));
    }

    [Fact]
    public void RejectsTemperaturesBelowAbsoluteZero()
    {
        var exception = Assert.Throws<ArgumentOutOfRangeException>(
            () => TemperatureConverter.CelsiusToFahrenheit(-274));

        Assert.Equal("celsius", exception.ParamName);
    }
}
