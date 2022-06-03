$(".rankListClick").on('click', function () {
    const contest_name = $(this).attr("contest_name");
    const username = $(this).attr("username");
    const data_region = $(this).attr("data_region");
    $.ajax({
        url: "/user_rank_list",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({
            "contest_name": contest_name,
            "username": username,
            "data_region": data_region
        }),
        dataType: "json",
        success: function (data) {
            const real_time_rank = data["real_time_rank"];
            trend_plot(real_time_rank);
        },
        error: function () {
            console.log("ajax to /user_rank_list error.")
        }
    })
});

let chartDom = document.getElementById('main');
let myChart = echarts.init(chartDom);
let option;

function trend_plot(rank_list) {
    option = {
        animationDuration: 10000,
        dataset: [
            {
                id: 'dataset_raw',
                source: rank_list
            }
        ],
        title: {
            text: 'Real Time User Rank',
            x: 'center'
        },
        tooltip: {
            order: 'valueDesc',
            trigger: 'axis'
        },
        xAxis: {
            type: 'category',
            nameLocation: 'middle'
        },
        yAxis: {
            name: 'Rank'
        },
        grid: {
            right: 140
        },
        series: [
            {
                type: 'line',
                datasetId: 'dataset_raw',
                showSymbol: false,
                encode: {
                    x: 'Minute',
                    y: 'Rank',
                    itemName: 'Minute',
                    tooltip: ['Rank']
                }
            }
        ]
    };
    myChart.setOption(option);
}

option && myChart.setOption(option);