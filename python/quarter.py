#!/usr/bin/env python
import sys
import update_dart_rain
import model
import scraping

def main():
    testing = False
    if len(sys.argv) > 1:
        testing = sys.argv[1] == 'testing' 
    scraping.level(testing)
    model.run_model(testing)    
if __name__ == '__main__':
    main()





