import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import useSWR from "swr";
import Pagination from "../../components/Pagination";
import { baseUrl } from "../../data/constants";
import ContestsUserNum from "../Contests/ContestsUserNum";

const ContestsTable = ({ contests }) => {
  return (
    <div className="overflow-x-auto">
      <table className="table">
        <thead>
          <tr className="bg-base-200">
            <th></th>
            <th>Predicted Contest</th>
            <th className="hidden md:table-cell">Started Time</th>
            <th className="hidden sm:table-cell">Predicted Time</th>
            <th>Official Result</th>
          </tr>
        </thead>
        <tbody>
          {contests.map((contest, i) => (
            <tr
              key={contest.titleSlug}
              className={
                contest.titleSlug.startsWith("bi") ? "bg-base-200" : undefined
              }
            >
              <th>{i + 1}</th>
              <td>
                <Link
                  className="link link-primary"
                  to={`/predicted/${contest.titleSlug}`}
                >
                  {contest.title}
                </Link>
              </td>
              <td className="hidden md:table-cell">
                {new Date(contest.startTime + "Z").toLocaleString()}
              </td>
              <td className="hidden sm:table-cell">
                {new Date(contest.predict_time + "Z").toLocaleString()}
              </td>
              <td>
                <div className="badge badge-secondary">
                  <a
                    className="link"
                    href={`https://leetcode.cn/contest/${contest.titleSlug}/ranking`}
                    target="_blank"
                    rel="noreferrer noopener"
                  >
                    LCCN
                  </a>
                </div>
                &nbsp;/&nbsp;
                <div className="badge badge-accent">
                  <a
                    className="link"
                    href={`https://leetcode.com/contest/${contest.titleSlug}/ranking`}
                    target="_blank"
                    rel="noreferrer noopener"
                  >
                    LCUS
                  </a>
                </div>
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

const PredictedContest = () => {
  useEffect(() => {
    document.title = "Predicted Contests";
  }, []);

  const pageSize = 10; // hard code `pageSize` temporarily
  const { pageNum: pageNumStr } = useParams();
  const pageNum = parseInt(pageNumStr) || 1;
  const skipNum = pageSize * (pageNum - 1);

  const {
    data: contests,
    isLoading,
    error,
  } = useSWR(
    `${baseUrl}/contests/?skip=${skipNum}&limit=${pageSize}`,
    (url) => fetch(url).then((r) => r.json()),
    { revalidateOnFocus: false }
  );

  // TODO: totalCount could +1 but won't refetch currently, a potential bug here.
  const { data: totalCount } = useSWR(
    `${baseUrl}/contests/count`,
    (url) => fetch(url).then((r) => r.json()),
    { revalidateOnFocus: false }
  );
  // console.log(`totalCount=${totalCount} pageNum=${pageNum}`);

  const [hypotheticalResult, setHypotheticalResult] = useState(null);

  if (!contests || isLoading)
    return (
      <div className="grid h-screen place-items-center ">
        <div>
          <progress className="progress w-56"></progress>
          <p className="text-center">Loading Contests</p>
        </div>
      </div>
    );

  if (error)
    return (
      <div className="grid h-screen place-items-center ">
        <div>
          <progress className="progress w-56"></progress>
          <p className="text-center">Error: {error.message}</p>
          <p className="text-center">Try Refresh</p>
        </div>
      </div>
    );

  return (
    <>
      <ContestsUserNum />
      {contests ? <ContestsTable contests={contests} /> : undefined}
      <Pagination
        totalCount={totalCount}
        pageNum={pageNum}
        pageURL={""}
        pageSize={pageSize}
      />
      <HypotheticalEntryForm
        titleSlug={contests[0].titleSlug}
        setHypotheticalResult={setHypotheticalResult}
      />
      <HypotheticalResult result={hypotheticalResult} />
    </>
  );
};

export default PredictedContest;
