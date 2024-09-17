import { useEffect } from "react";
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
    </>
  );
};

export default PredictedContest;
