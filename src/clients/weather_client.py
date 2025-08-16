import requests
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json

from ..utils.config import Config


class WeatherClient:
    """Client for OpenWeatherMap API"""

    def __init__(self):
        """Initialize the weather client"""
        self.api_key = Config.OPENWEATHER_API_KEY
        self.base_url = Config.OPENWEATHER_BASE_URL
        self.timeout = 10  # seconds

        if not self.api_key:
            print("⚠️ OpenWeather API key not found - weather features disabled")

    def get_forecast(self, location: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Get weather forecast for a location and date range

        Args:
            location: City name, country (e.g., "Barcelona, Spain")
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Dict with weather information or error details
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "Weather API key not configured",
                "data": "Weather information is currently unavailable."
            }

        try:
            # First, get coordinates for the location
            coords_result = self._get_coordinates(location)
            if not coords_result["success"]:
                return coords_result

            lat = coords_result["lat"]
            lon = coords_result["lon"]
            location_name = coords_result["name"]

            # Get current weather
            current_weather = self._get_current_weather(lat, lon)

            # Get 5-day forecast (free tier limitation)
            forecast_weather = self._get_forecast_data(lat, lon)

            # Process and format the weather data
            formatted_data = self._format_weather_data(
                location_name, start_date, end_date,
                current_weather, forecast_weather
            )
            print(formatted_data)

            return {
                "success": True,
                "data": formatted_data
            }

        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"Weather API request failed: {str(e)}",
                "data": "Unable to retrieve weather information at this time."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Weather processing error: {str(e)}",
                "data": "Weather information is temporarily unavailable."
            }

    def _get_coordinates(self, location: str) -> Dict[str, Any]:
        """Get coordinates for a location using geocoding API"""
        url = f"http://api.openweathermap.org/geo/1.0/direct"
        params = {
            "q": location,
            "limit": 1,
            "appid": self.api_key
        }

        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()

        if not data:
            return {
                "success": False,
                "error": f"Location '{location}' not found",
                "data": f"Could not find weather data for '{location}'. Please check the location name."
            }

        location_data = data[0]
        return {
            "success": True,
            "lat": location_data["lat"],
            "lon": location_data["lon"],
            "name": f"{location_data['name']}, {location_data.get('country', '')}"
        }

    def _get_current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get current weather for coordinates"""
        url = f"{self.base_url}/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric"
        }

        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()

        return response.json()

    def _get_forecast_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get 5-day forecast for coordinates"""
        url = f"{self.base_url}/forecast"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric"
        }

        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()

        return response.json()

    def _format_weather_data(self, location: str, start_date: str, end_date: str,
                             current: Dict, forecast: Dict) -> str:
        """Format weather data into readable text with daily breakdown"""

        # Parse dates
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return f"Weather forecast for {location}: Date format error - using current conditions only."

        # Start building the weather report
        report = f"Weather forecast for {location} ({start_date} to {end_date}):\n\n"

        # Current conditions
        current_temp = current["main"]["temp"]
        current_desc = current["weather"][0]["description"].title()
        current_humidity = current["main"]["humidity"]
        current_wind = current["wind"]["speed"]
        feels_like = current["main"]["feels_like"]

        report += f"Current conditions:\n"
        report += f"- Temperature: {current_temp:.1f}°C ({current_temp * 9 / 5 + 32:.1f}°F), feels like {feels_like:.1f}°C\n"
        report += f"- Conditions: {current_desc}\n"
        report += f"- Humidity: {current_humidity}%\n"
        report += f"- Wind speed: {current_wind:.1f} m/s\n\n"

        # Daily breakdown
        forecast_items = forecast["list"]

        # Group forecast by day
        daily_forecasts = {}
        for item in forecast_items:
            forecast_dt = datetime.fromtimestamp(item["dt"])

            # Only include dates within the requested range
            if start_dt.date() <= forecast_dt.date() <= end_dt.date():
                date_key = forecast_dt.date()

                if date_key not in daily_forecasts:
                    daily_forecasts[date_key] = []
                daily_forecasts[date_key].append(item)

        if daily_forecasts:
            report += "Daily forecast breakdown:\n\n"

            for date_key in sorted(daily_forecasts.keys()):
                day_items = daily_forecasts[date_key]
                day_name = date_key.strftime("%A")
                date_str = date_key.strftime("%B %d")

                # Calculate daily stats
                temps = [item["main"]["temp"] for item in day_items]
                conditions = [item["weather"][0]["description"] for item in day_items]
                humidity_values = [item["main"]["humidity"] for item in day_items]
                wind_speeds = [item["wind"]["speed"] for item in day_items]

                # Check for rain
                rain_items = [item for item in day_items if "rain" in item.get("rain", {})]
                has_rain = len(rain_items) > 0
                rain_chance = len(rain_items) / len(day_items) * 100 if day_items else 0

                # Get most common condition
                condition_counts = {}
                for condition in conditions:
                    condition_counts[condition] = condition_counts.get(condition, 0) + 1
                most_common_condition = max(condition_counts, key=condition_counts.get).title()

                min_temp = min(temps)
                max_temp = max(temps)
                avg_humidity = sum(humidity_values) / len(humidity_values)
                avg_wind = sum(wind_speeds) / len(wind_speeds)

                report += f"**{day_name}, {date_str}:**\n"
                report += f"  • Temperature: {min_temp:.1f}°C to {max_temp:.1f}°C ({min_temp * 9 / 5 + 32:.1f}°F to {max_temp * 9 / 5 + 32:.1f}°F)\n"
                report += f"  • Conditions: {most_common_condition}\n"
                report += f"  • Humidity: {avg_humidity:.0f}%\n"
                report += f"  • Wind: {avg_wind:.1f} m/s\n"

                if has_rain:
                    report += f"  • Rain: {rain_chance:.0f}% chance of precipitation\n"

                report += "\n"

            # Overall trip summary
            all_temps = [item["main"]["temp"] for day_items in daily_forecasts.values() for item in day_items]
            overall_rain_items = [item for day_items in daily_forecasts.values() for item in day_items if
                                  "rain" in item.get("rain", {})]
            total_forecasts = sum(len(day_items) for day_items in daily_forecasts.values())

            if all_temps:
                trip_min = min(all_temps)
                trip_max = max(all_temps)
                overall_rain_chance = len(overall_rain_items) / total_forecasts * 100 if total_forecasts else 0

                report += f"Trip overview:\n"
                report += f"- Overall temperature range: {trip_min:.1f}°C to {trip_max:.1f}°C\n"
                report += f"- Overall rain probability: {overall_rain_chance:.0f}%\n"

                if overall_rain_chance > 50:
                    report += f"- Rain expected frequently during trip\n"
                elif overall_rain_chance > 20:
                    report += f"- Some rain possible during trip\n"
                else:
                    report += f"- Mostly dry conditions expected\n"

        else:
            report += "Detailed daily forecast: Available for next 5 days only from today.\n"
            report += "For longer-range planning, check closer to your travel dates.\n"

        return report

    def test_connection(self) -> Dict[str, Any]:
        """Test the weather API connection"""
        if not self.api_key:
            return {
                "success": False,
                "message": "API key not configured"
            }

        try:
            # Test with a simple location
            result = self._get_coordinates("London, UK")
            if result["success"]:
                return {
                    "success": True,
                    "message": "Weather API connection successful"
                }
            else:
                return {
                    "success": False,
                    "message": f"API test failed: {result['error']}"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection test error: {str(e)}"
            }