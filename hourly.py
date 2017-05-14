#!/usr/bin/env python
import sys
import update_dart_rain
import nevis
import model
import scraping
def main():
    testing = False
    if len(sys.argv) > 1:
        testing = sys.argv[1] == 'testing' 
    scraping.update_forecast_rainfall(testing)
    update_dart_rain.rain(testing)
    scraping.level(testing)
    model.run_model(testing)
if __name__ == '__main__':
    main()





