#!/usr/bin/env python

from model import get_data, add_missing_timestamps, calculate_rain, model, create_json, upload_json




river = "dart"
limit = 200

data = get_data(river, limit)

data = add_missing_timestamps(data)


data = calculate_rain(data)

#pretty_print(data)



data = model(data)

#pretty_print2(data)

output = create_json(river, data)


upload_json(output, river + '.json')

