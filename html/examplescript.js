google.load("visualization", "1", {packages:["corechart"]});
google.setOnLoadCallback(drawChart);

function drawChart() {
    var jsonData = $.ajax({
        url: "dart.json",
        dataType: "json",
        async: false
    }).done(function (results) {
        updated_date = new Date(results.current_time / 1000);
        document.querySelector('#updated').innerHTML = "Latest model run:   " + updated_date.toLocaleDateString() + " " + updated_date.toLocaleTimeString();
        text = results.text;

        if (text.length < 5){
          document.querySelector('#yesno').innerHTML = text;
        } else {
          document.querySelector('#message').innerHTML = text;
        }

        var data = new google.visualization.DataTable();
        data.addColumn('datetime', 'Time');
        data.addColumn('number', 'Rain');
        data.addColumn('number', 'Forecast');
        data.addColumn('number', 'Level');
        data.addColumn('number', 'Prediction');

        $.each(results.values, function (i, row) {
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
    });  
    
}

$(window).resize(function(){
      drawChart();
});
