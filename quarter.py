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
    update_dart_level.level(testing)
    get_radar.get_png()
if __name__ == '__main__':
    main()





