import ReactEcharts from "echarts-for-react";

const ContestsUserNumStackedArea = ({ contests }) => {
  contests.sort((a, b) => new Date(a.startTime) - new Date(b.startTime));
  // console.log(contests);
  const titles = contests.map((contest) =>
    contest.title.replace(/eekly Contest /g, "")
  );
  const usNums = contests.map((contest) => contest.user_num_us);
  const cnNums = contests.map((contest) => contest.user_num_cn);
  const option = {
    title: {
      text: "Number of Contest Entrants",
      x: "center",
    },
    color: ["#ee6666", "#5470c6"],
    tooltip: {
      trigger: "axis",
      axisPointer: {
        type: "cross",
        label: {
          backgroundColor: "#6a7985",
        },
      },
    },
    legend: {
      data: ["US", "CN"],
      left: "80%",
    },
    toolbox: {
      feature: {
        saveAsImage: {},
      },
    },
    grid: {
      left: "3%",
      right: "4%",
      bottom: "3%",
      containLabel: true,
    },
    xAxis: [
      {
        type: "category",
        boundaryGap: false,
        name: "Contest",
        // axisLabel: {
        //     rotate: 75,
        //   },
        data: titles,
      },
    ],
    yAxis: [
      {
        type: "value",
        name: "User Count",
      },
    ],
    series: [
      {
        name: "CN",
        type: "line",
        stack: "Total",
        label: {
          show: true,
          position: "top",
        },
        areaStyle: {},
        emphasis: {
          focus: "series",
        },
        data: cnNums,
      },
      {
        name: "US",
        type: "line",
        stack: "Total",
        label: {
          show: true,
          position: "top",
        },
        areaStyle: {},
        emphasis: {
          focus: "series",
        },
        data: usNums,
      },
    ],
  };

  return (
    <ReactEcharts
      option={option}
      // theme="dark"
      // lazyUpdate={true}
      // opts={{renderer: "svg"}}
      // style={{
      //     height: "25em",
      // }}
    />
  );
};

export default ContestsUserNumStackedArea;
