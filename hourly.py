#!/usr/bin/env python
import sys
import forecast
import update_dart_level
import update_dart_rain
import nevis
import model

def main():
    testing = False
    if len(sys.argv) > 1:
        testing = sys.argv[1] == 'testing' 
    forecast.update_forecast_rainfall(testing)
    model.run_model(testing)
    
    update_dart_level.level(testing)
    update_dart_rain.rain(testing)
    nevis.rain_and_level(testing)
if __name__ == '__main__':
    main()





