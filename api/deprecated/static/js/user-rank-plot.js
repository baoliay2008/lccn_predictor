$(".rankListClick").on("click", function () {
  const contest_name = $(this).attr("contest_name");
  const username = $(this).attr("username");
  const data_region = $(this).attr("data_region");
  $.ajax({
    url: "/user_rank_list",
    type: "POST",
    contentType: "application/json",
    data: JSON.stringify({
      contest_name: contest_name,
      username: username,
      data_region: data_region,
    }),
    dataType: "json",
    success: function (data) {
      const real_time_rank = data["real_time_rank"];
      trend_plot(real_time_rank, username);
      $("#question_plot").hide();
      $("#user_rank_plot").show();
    },
    error: function () {
      console.log("ajax to /user_rank_list error.");
    },
  });
});

let chartDom = document.getElementById("user_rank_plot");
let myChart = echarts.init(chartDom);
let option;

function trend_plot(rank_list, username) {
  const users = [username];
  const datasetWithFilters = [];
  const seriesList = [];
  echarts.util.each(users, function (user) {
    var datasetId = "dataset_" + user;
    datasetWithFilters.push({
      id: datasetId,
      fromDatasetId: "dataset_raw",
      transform: {
        type: "filter",
        config: {
          and: [{ dimension: "User", "=": user }],
        },
      },
    });
    seriesList.push({
      type: "line",
      datasetId: datasetId,
      showSymbol: false,
      name: user,
      endLabel: {
        show: true,
        formatter: function (params) {
          return params.value[1] + ": " + params.value[2];
        },
      },
      labelLayout: {
        moveOverlap: "shiftY",
      },
      emphasis: {
        focus: "series",
      },
      encode: {
        x: "Minute",
        y: "Rank",
        label: ["User", "Rank"],
        itemName: "Minute",
        tooltip: ["Rank"],
      },
    });
  });
  option = {
    animationDuration: 10000,
    dataset: [
      {
        id: "dataset_raw",
        source: rank_list,
      },
      ...datasetWithFilters,
    ],
    title: {
      text: "User Real Time Rank",
      x: "center",
    },
    tooltip: {
      order: "valueDesc",
      trigger: "axis",
    },
    xAxis: {
      type: "category",
      name: "Minute",
    },
    yAxis: {
      name: "Rank",
    },
    grid: {
      right: 140,
    },
    series: seriesList,
  };
  myChart.setOption(option);
}

option && myChart.setOption(option);
