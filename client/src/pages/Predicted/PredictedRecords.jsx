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

const PredictedRecords = () => {
  const pageSize = 25; // hard code `pageSize` temporarily

  const { titleSlug, pageNum: pageNumStr } = useParams();
  const pageNum = parseInt(pageNumStr) || 1;
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
