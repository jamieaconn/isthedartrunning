#!/usr/bin/env python
import sys
import forecast
import update_dart_level
import update_dart_rain
import nevis
import model
import get_radar

def main():
    testing = False
    if len(sys.argv) > 1:
        testing = sys.argv[1] == 'testing' 
    model.run_model(testing)
    get_radar.get_png()

    update_dart_level.level(testing)
    update_dart_rain.rain(testing)
if __name__ == '__main__':
    main()





