#!/usr/bin/env python
import sys
import update_dart_level
import update_dart_rain
import nevis
import model

def main():
    testing = False
    if len(sys.argv) > 1:
        testing = sys.argv[1] == 'testing' 
    update_dart_level.level(testing)
    update_dart_rain.rain(testing)
    model.run_model(testing)
if __name__ == '__main__':
    main()





