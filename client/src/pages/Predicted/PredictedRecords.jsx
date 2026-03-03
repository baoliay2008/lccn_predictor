import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faUser,
  faSearch,
  faLeftLong,
} from "@fortawesome/free-solid-svg-icons";

import useSWR from "swr";
import Pagination from "../../components/Pagination";
import QuestionFinishedChart from "../../components/charts/QuestionFinishedChart";
import RealTimeRankChart from "../../components/charts/RealTimeRankChart";
import { baseUrl } from "../../data/constants";
import { trendColorsHSL } from "../../utils";

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
          <tr className="bg-base-200">
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

const HypotheticalEntryForm = ({ titleSlug, setHypotheticalResult }) => {
  const [username, setUsername] = useState("");
  const [dataRegion, setDataRegion] = useState("US");
  const [rank, setRank] = useState("");
  const [score, setScore] = useState("");
  const [finishTime, setFinishTime] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    const response = await fetch(`${baseUrl}/contest-records/hypothetical-entry`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contest_name: titleSlug,
        username,
        data_region: dataRegion,
        rank: parseInt(rank),
        score: parseInt(score),
        finish_time: new Date(finishTime).toISOString(),
      }),
    });
    const result = await response.json();
    setHypotheticalResult(result);
  };

  return (
    <form onSubmit={handleSubmit} className="container mx-auto text-center">
      <div className="form-control">
        <label className="input-group">
          <span>Username</span>
          <input
            type="text"
            placeholder="Username"
            className="input input-bordered"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </label>
      </div>
      <div className="form-control">
        <label className="input-group">
          <span>Data Region</span>
          <select
            className="select select-bordered"
            value={dataRegion}
            onChange={(e) => setDataRegion(e.target.value)}
            required
          >
            <option value="US">US</option>
            <option value="CN">CN</option>
          </select>
        </label>
      </div>
      <div className="form-control">
        <label className="input-group">
          <span>Rank</span>
          <input
            type="number"
            placeholder="Rank"
            className="input input-bordered"
            value={rank}
            onChange={(e) => setRank(e.target.value)}
            required
          />
        </label>
      </div>
      <div className="form-control">
        <label className="input-group">
          <span>Score</span>
          <input
            type="number"
            placeholder="Score"
            className="input input-bordered"
            value={score}
            onChange={(e) => setScore(e.target.value)}
            required
          />
        </label>
      </div>
      <div className="form-control">
        <label className="input-group">
          <span>Finish Time</span>
          <input
            type="datetime-local"
            className="input input-bordered"
            value={finishTime}
            onChange={(e) => setFinishTime(e.target.value)}
            required
          />
        </label>
      </div>
      <button className="btn btn-primary" type="submit">
        Calculate Hypothetical Rating Change
      </button>
    </form>
  );
};

const HypotheticalResult = ({ result }) => {
  if (!result) return null;

  return (
    <div className="container mx-auto text-center">
      <h2>Hypothetical Rating Change</h2>
      <p>Old Rating: {result.old_rating.toFixed(2)}</p>
      <p>New Rating: {result.new_rating.toFixed(2)}</p>
      <p>Delta Rating: {result.delta_rating.toFixed(2)}</p>
    </div>
  );
};

const PredictedRecords = () => {
  const pageSize = 25; // hard code `pageSize` temporarily

  const { titleSlug, pageNum: pageNumStr } = useParams();
  const pageNum = parseInt(pageNumStr) || 1;
  const skipNum = pageSize * (pageNum - 1);

  const [predictedRecordsURL, setPredictedRecordsURL] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [user, setUser] = useState(null);
  const [hypotheticalResult, setHypotheticalResult] = useState(null);

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

  // console.log(`user=${user} ${user?.username} ${user?.data_region}`);

  const { data: rankData } = useSWR(
    user
      ? [
          `${baseUrl}/contest-records/real-time-rank`,
          JSON.stringify({
            contest_name: titleSlug,
            user: user,
          }),
        ]
      : null,
    ([url, body]) =>
      fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: body,
      }).then((r) => r.json()),
    { revalidateOnFocus: false }
  );
  const rankList = rankData?.real_time_rank;
  // console.log(`rankData=${rankData} rankList=${rankList} ${rankList?.length} ${!rankList}`)

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
          pageURL={`/predicted/${titleSlug}`}
          pageSize={pageSize}
        />
      )}

      <HypotheticalEntryForm
        titleSlug={titleSlug}
        setHypotheticalResult={setHypotheticalResult}
      />
      <HypotheticalResult result={hypotheticalResult} />

      <input type="checkbox" id="my-modal-4" className="modal-toggle" />
      <label htmlFor="my-modal-4" className="modal cursor-pointer">
        <label className="modal-box relative" htmlFor="">
          <div className="container mx-auto text-center">
            {rankList && <RealTimeRankChart user={user} rankList={rankList} />}
            {!rankList && (
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
