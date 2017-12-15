import argparse
import scraping
import modelLib

def main(timing, testing):
	if testing:
		print "Running model on", timing, "in testing mode"
	else:
		print "Running model on", timing
	print

	if timing == "hour": 
		scraping.update_forecast_rainfall(testing)
		scraping.rain(testing)
		scraping.level(testing)
		scraping.get_radar_images(testing)
		modelLib.run(testing)

	elif timing == "half":
		scraping.rain(testing)
		scraping.level(testing)
		modelLib.run(testing)
	elif timing == "quarter":
		scraping.level(testing)
		modelLib.run(testing)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Run the model')
    parser.add_argument('timing', type=str, choices=["hour", "half", "quarter"], help='which version to run')
    parser.add_argument('-testing', default=False, action="store_true", help='run code in testing mode')
    args = parser.parse_args()
    main(args.timing, args.testing)
