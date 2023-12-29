google.charts.load('current', {'packages':['corechart']});
// Set a callback function to be executed when the API has loaded
google.charts.setOnLoadCallback(drawChart);
window.dataLayer = window.dataLayer || [];

function drawChart() {
    var jsonData = $.ajax({
        url: "https://europe-west2-even-autonomy-239218.cloudfunctions.net/fetch_data",
        dataType: "json",
        async: false
    }).done(function (results) {
        updated_date = new Date(results.data.current_time*1000);
        minutes_since_updated = (Date.now() - (results.data.current_time*1000))/(1000*60)
        console.log(minutes_since_updated)
        document.querySelector('#updated').innerHTML = "Latest model run:   " + updated_date.toLocaleDateString() + " " + updated_date.toLocaleTimeString();
        text = results.data.text;

        if (minutes_since_updated > 120) { // if it's not updated in the last 2 hours
          document.querySelector('#errormain').innerHTML = "NOT SURE";
          document.querySelector('#errorminor').innerHTML = "Something is broken...";
        } else {
        
            if (text.length < 5){
              document.querySelector('#yesno').innerHTML = text;
            } else {
              document.querySelector('#message').innerHTML = text;
            }

            // sort the graph data by timestamp
            results.data.values.sort((a, b) => a.timestamp - b.timestamp);

            var data = new google.visualization.DataTable();
            data.addColumn('datetime', 'Time');
            data.addColumn('number', 'Rain');
            data.addColumn('number', 'Forecast');
            data.addColumn('number', 'Level');
            data.addColumn('number', 'Prediction');

            $.each(results.data.values, function (i, row) {
                data.addRow([
                    (new Date(row.timestamp / 1000)), 
                    parseFloat(row.rain),
                    parseFloat(row.forecast),
                    parseFloat(row.level),
                    parseFloat(row.predict)
                ]);
            });
            if (screen.availWidth < 400) {
                var legend = {position: 'top', textStyle: {fontSize: 8}};
            } else {
                var legend = {position: 'top'};
            }
            var options = {
                legend: legend,
                seriesType: 'line',
                lineWidth: 4,
                hAxis : {
                    format: 'E HH:mm'
                },
                vAxis : {
                    viewWindow: {
                        max: 2.5,
                        min: 0
                    }
                },
                series : {
                    0: { type: 'bars' },
                    1: { type: 'bars' },
                    3: { lineDashStyle: [4, 4] }
                },
                colors: ['#080808','#A9A9A9', '#1c91c0', '#1c91c0']

            };

            var chart = new google.visualization.ComboChart($('#chart_div').get(0));
            chart.draw(data, options);
         }
    });  
    
}

$(window).resize(function(){
      drawChart();
});
