google.load("visualization", "1", {packages:["corechart"]});
google.setOnLoadCallback(drawChart);





function drawChart() {
    var jsonData = $.ajax({
        url: "dart.json",
        dataType: "json",
        async: false
    }).done(function (results) {
        document.querySelector('.updated').innerHTML = "Updated:   " + new Date(results.current_time / 1000);
        var data = new google.visualization.DataTable();
        data.addColumn('datetime', 'Time');
        data.addColumn('number', 'Rain');
        data.addColumn('number', 'Level');
        data.addColumn('number', 'Prediction');

        $.each(results.values, function (i, row) {
            data.addRow([
                (new Date(row.timestamp / 1000)), 
                parseFloat(row.rain),
                parseFloat(row.level),
                parseFloat(row.predict)
            ]);
        });

        var options = {
            title : "The River Dart",
            seriesType: 'line',
            lineWidth: 4,
            hAxis : {
                format: 'E HH:mm'
            },
            vAxis : {
                viewWindow: {
                    max: 2,
                    min: 0
                }
            },
            series : {
                0: { type: 'bars' },
                2: { lineDashStyle: [4, 4] }
            },
            colors: ['#999999', '#1c91c0', '#1c91c0']

        };

        var chart = new google.visualization.ComboChart($('#chart_div').get(0));
        chart.draw(data, options);


    });  
    
}

$(window).resize(function(){
      drawChart();
});
