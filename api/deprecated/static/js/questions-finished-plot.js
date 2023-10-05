window.onload = function () {
  const contest_name = $("#question_plot").attr("contest_name");
  if (!contest_name) {
    console.log("not found");
    return;
  }
  $.ajax({
    url: "/questions_finished_list",
    type: "POST",
    contentType: "application/json",
    data: JSON.stringify({
      contest_name: contest_name,
    }),
    dataType: "json",
    success: function (data) {
      const real_time_count = data["real_time_count"];
      trend_plot(real_time_count);
    },
    error: function () {
      console.log("ajax to /questions_finished_list error.");
    },
  });
};

let chartDom = document.getElementById("question_plot");
let myChart = echarts.init(chartDom);
let option;

function trend_plot(rank_list) {
  const questions = ["Q1", "Q2", "Q3", "Q4"];
  const datasetWithFilters = [];
  const seriesList = [];
  echarts.util.each(questions, function (question) {
    var datasetId = "dataset_" + question;
    datasetWithFilters.push({
      id: datasetId,
      fromDatasetId: "dataset_raw",
      transform: {
        type: "filter",
        config: {
          and: [{ dimension: "Question", "=": question }],
        },
      },
    });
    seriesList.push({
      type: "line",
      datasetId: datasetId,
      showSymbol: false,
      name: question,
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
        y: "Count",
        label: ["Question", "Count"],
        itemName: "Minute",
        tooltip: ["Count"],
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
      text: "Question Finished Count",
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
      name: "Accepted",
    },
    grid: {
      right: 140,
    },
    series: seriesList,
  };
  myChart.setOption(option);
}

option && myChart.setOption(option, (notMerge = true));
