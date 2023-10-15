import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";

import ReactEcharts from "echarts-for-react";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faUser,
  faSearch,
  faLeftLong,
} from "@fortawesome/free-solid-svg-icons";

import useSWR from "swr";
import Pagination from "../../components/Pagination";
import { baseUrl } from "../../data/constants";
import { trendColorsHSL } from "../../utils";

const QuestionFinishedChart = ({ questionsRaw }) => {
  // console.log("QuestionFinishedChart questionsRaw=", questionsRaw);
  const questions = [...questionsRaw].sort((a, b) =>
    a.credit === b.credit ? a.question_id - b.question_id : a.credit - b.credit
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

const RealTimeRankChart = ({ user }) => {
  // console.log(`user=${user} ${user?.username} ${user?.data_region}`);

  const { titleSlug } = useParams();

  const { data } = useSWR(
    [
      `${baseUrl}/contest-records/real-time-rank`,
      JSON.stringify({
        contest_name: titleSlug,
        user: user,
      }),
    ],
    ([url, body]) =>
      fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: body,
      }).then((r) => r.json()),
    { revalidateOnFocus: false }
  );
  const rankList = data?.real_time_rank;
  if (!rankList) return null;

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

const PredictedRecordsSearch = ({
  titleSlug,
  setPredictedRecordsURL,
  isSearching,
  setIsSearching,
}) => {
  const [userName, setUserName] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    setPredictedRecordsURL(
      `${baseUrl}/contest-records/user?contest_name=${titleSlug}&username=${userName}&archived=false`
    );
    setIsSearching(true);
  };

  const navigate = useNavigate();
  const handleBack = (e) => {
    if (isSearching) {
      e.preventDefault();
      setIsSearching(false);
    } else {
      navigate("/");
    }
  };

  return (
    <div className="container mx-auto text-center">
      <form onSubmit={(e) => handleSubmit(e)}>
        <div
          style={{
            marginTop: "1em",
            marginBottom: "1em",
          }}
        >
          <button
            className="btn"
            type="button"
            onClick={(e) => handleBack(e)}
            style={{
              marginRight: "1em",
            }}
          >
            <FontAwesomeIcon icon={faLeftLong} size="lg" />
          </button>

          <label>
            <FontAwesomeIcon icon={faUser} size="lg" />
          </label>
          <input
            type="text"
            id="Username"
            placeholder="Username"
            required={true}
            onChange={(e) => setUserName(e.target.value)}
            className="input input-bordered input-primary w-1/2 max-w-xs"
            style={{
              marginLeft: "0.5em",
              marginRight: "1em",
            }}
          />
          <button className="btn" type="submit">
            <FontAwesomeIcon icon={faSearch} size="lg" />
          </button>
        </div>
      </form>
    </div>
  );
};

const PredictedRecordsTable = ({ predictedRecords, setUser }) => {
  return (
    <div className="overflow-x-auto">
      <table className="table table-compact w-full">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Username</th>
            <th className="hidden md:table-cell">Region</th>
            <th className="hidden sm:table-cell">Old Rating</th>
            <th>Delta</th>
            <th>New Rating</th>
            <th>Trend</th>
          </tr>
        </thead>
        <tbody>
          {predictedRecords.map((record, i) => (
            <tr key={i} className="hover">
              <th>#{record.rank}</th>
              <td>
                {record.data_region === "CN" ? (
                  <a
                    className="link link-secondary link-hover"
                    href={`https://leetcode.cn/u/${record.username}`}
                    target="_blank"
                    rel="noreferrer noopener"
                  >
                    {record.username}
                  </a>
                ) : (
                  <a
                    className="link link-accent link-hover"
                    href={`https://leetcode.com/${record.username}`}
                    target="_blank"
                    rel="noreferrer noopener"
                  >
                    {record.username}
                  </a>
                )}
              </td>
              <td className="hidden md:table-cell">{record.country_name}</td>
              <td className="hidden sm:table-cell">
                {record.old_rating.toFixed(2)}
              </td>
              <td
                style={{
                  backgroundColor:
                    record.delta_rating > 0
                      ? `hsla(${trendColorsHSL.up}, ${
                          0.1 + record.delta_rating / 100
                        })`
                      : `hsla(${trendColorsHSL.down}, ${
                          0.2 - record.delta_rating / 100
                        })`,
                }}
              >
                {record.delta_rating > 0
                  ? "+" + record.delta_rating.toFixed(2)
                  : record.delta_rating.toFixed(2)}
              </td>
              <td>{record.new_rating.toFixed(2)}</td>
              <td>
                <label
                  htmlFor="my-modal-4"
                  className="btn btn-xs"
                  onClick={() =>
                    setUser({
                      username: record.username,
                      data_region: record.data_region,
                    })
                  }
                >
                  plot
                </label>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const PredictedRecords = () => {
  const pageSize = 25; // hard code `pageSize` temporarily

  const { titleSlug, pageNum } = useParams();
  const skipNum = pageSize * (pageNum - 1);

  const [predictedRecordsURL, setPredictedRecordsURL] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [user, setUser] = useState(null);

  useEffect(() => {
    document.title = `${titleSlug} 🔮`;
  }, [titleSlug]);

  useEffect(() => {
    if (!isSearching) {
      setPredictedRecordsURL(
        `${baseUrl}/contest-records/?contest_name=${titleSlug}&archived=false&skip=${skipNum}&limit=${pageSize}`
      );
    }
    setUser(null);
  }, [pageNum, isSearching]);

  const { data: totalCount } = useSWR(
    `${baseUrl}/contest-records/count?contest_name=${titleSlug}&archived=false`,
    (url) => fetch(url).then((r) => r.json()),
    { revalidateOnFocus: false }
  );

  const { data: questionsRaw } = useSWR(
    [
      `${baseUrl}/questions/`,
      JSON.stringify({
        contest_name: titleSlug,
      }),
    ],
    ([url, body]) =>
      fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: body,
      }).then((r) => r.json()),
    { revalidateOnFocus: false }
  );
  // console.log(`questionsRaw=${questionsRaw}`);

  // console.log(`predictedRecordsURL=${predictedRecordsURL}`);
  const {
    data: predictedRecords,
    isLoading,
    error,
  } = useSWR(predictedRecordsURL, (url) => fetch(url).then((r) => r.json()), {
    revalidateOnFocus: false,
  });

  // if (predictedRecordsURL === null) return;
  // console.log(`predictedRecords=${predictedRecords}`);

  if (!predictedRecords || isLoading)
    return (
      <div className="grid h-screen place-items-center ">
        <div>
          <progress className="progress w-56"></progress>
          <p className="text-center">Loading Records</p>
        </div>
      </div>
    );

  if (error)
    return (
      <div className="grid h-screen place-items-center ">
        <div>
          <progress
            className="progress progress-error w-56"
            value="100"
            max="100"
          ></progress>
          <p className="text-center">Error! Try to revisit later!</p>
        </div>
      </div>
    );

  return (
    <>
      {questionsRaw && (
        <div className="container mx-auto text-center">
          <QuestionFinishedChart questionsRaw={questionsRaw} />
        </div>
      )}

      <h1 className="text-center">{titleSlug.split("-").join(" ")}</h1>

      <PredictedRecordsSearch
        titleSlug={titleSlug}
        setPredictedRecordsURL={setPredictedRecordsURL}
        isSearching={isSearching}
        setIsSearching={setIsSearching}
      />
      <PredictedRecordsTable
        predictedRecords={predictedRecords}
        setUser={setUser}
      />
      {!isSearching && (
        <Pagination
          totalCount={totalCount}
          pageNum={pageNum}
          pageSize={pageSize}
          titleSlug={titleSlug}
        />
      )}

      <input type="checkbox" id="my-modal-4" className="modal-toggle" />
      <label htmlFor="my-modal-4" className="modal cursor-pointer">
        <label className="modal-box relative" htmlFor="">
          <div className="container mx-auto text-center">
            {user && <RealTimeRankChart user={user} />}
            {!user && (
              <div>
                <progress className="progress w-56"></progress>
                <p className="text-center">Loading Real Time Rank</p>
              </div>
            )}
          </div>
        </label>
      </label>
    </>
  );
};

export default PredictedRecords;
