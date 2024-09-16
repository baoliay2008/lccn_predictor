import ReactEcharts from "echarts-for-react";

const QuestionFinishedChart = ({ questionsRaw }) => {
  // console.log("QuestionFinishedChart questionsRaw=", questionsRaw);
  const questions = [...questionsRaw].sort((a, b) =>
    a.credit === b.credit ? a.qi - b.qi : a.credit - b.credit
  );

  const real_time_count = [["Minute", "Question", "Count"]];
  for (let i = 1; i <= questions.length; i++) {
    for (let j = 1; j <= questions[0].real_time_count?.length; j++) {
      real_time_count.push([
        j,
        `Q${i}`,
        questions[i - 1].real_time_count[j - 1],
      ]);
    }
  }

  const questionsId = ["Q1", "Q2", "Q3", "Q4"];
  const datasetWithFilters = [];
  const seriesList = [];

  questionsId.forEach((id) => {
    const datasetId = "dataset_" + id;
    datasetWithFilters.push({
      id: datasetId,
      fromDatasetId: "dataset_raw",
      transform: {
        type: "filter",
        config: {
          and: [{ dimension: "Question", "=": id }],
        },
      },
    });
    seriesList.push({
      type: "line",
      datasetId: datasetId,
      showSymbol: false,
      name: id,
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

  const option = {
    animation: true,
    animationDuration: 10000,
    dataset: [
      {
        id: "dataset_raw",
        source: real_time_count,
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
      // axisLabel: {
      //   rotate: 45,
      //   margin: 1
      // }
    },
    grid: {
      left: "70em",
      right: "70em",
    },
    series: seriesList,
  };

  // console.log("question option= ", option);
  return (
    <ReactEcharts
      option={option}
      // theme="dark"
      // lazyUpdate={true}
      // opts={{renderer: "svg"}}
      style={{
        height: "25em",
      }}
    />
  );
};

export default QuestionFinishedChart;
