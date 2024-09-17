import ReactEcharts from "echarts-for-react";

const RealTimeRankChart = ({ user, rankList }) => {
  const realTimeRank = [["Minute", "Username", "Rank"]];
  for (let j = 1; j <= rankList.length; j++) {
    realTimeRank.push([j, user.username, rankList[j - 1]]);
  }

  const users = [user.username];
  const datasetWithFilters = [];
  const seriesList = [];

  // console.log("users", users);
  // console.log("realTimeRank", realTimeRank);

  users.forEach((username) => {
    const datasetId = "dataset_" + username;
    datasetWithFilters.push({
      id: datasetId,
      fromDatasetId: "dataset_raw",
      transform: {
        type: "filter",
        config: {
          and: [{ dimension: "Username", "=": username }],
        },
      },
    });
    seriesList.push({
      type: "line",
      datasetId: datasetId,
      showSymbol: false,
      name: username,
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
        label: ["Username", "Rank"],
        itemName: "Minute",
        tooltip: ["Rank"],
      },
    });
  });

  const option = {
    animationDuration: 10000,
    dataset: [
      {
        id: "dataset_raw",
        source: realTimeRank,
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
      axisLabel: {
        rotate: 45,
        margin: 1,
      },
    },
    grid: {
      // left:"70em",
      right: "70em",
    },
    series: seriesList,
  };

  // console.log("realTimeRank option=", option);

  return (
    <ReactEcharts
      option={option}
      // theme="dark"
      // lazyUpdate={true}
      // opts={{renderer: "svg"}}
      style={{ height: "25em" }}
    />
  );
};

export default RealTimeRankChart;
