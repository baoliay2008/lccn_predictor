import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faAnglesLeft, faAnglesRight } from "@fortawesome/free-solid-svg-icons";
import { Link } from "react-router-dom";

const Pagination = ({ totalCount, pageNum, pageURL, pageSize }) => {
  const maxPageNum = Math.ceil(totalCount / pageSize);
  return (
    <div
      className="container mx-auto text-center"
      style={{
        marginTop: "0.5em",
        marginBottom: "1.0em",
      }}
    >
      <div className="join">
        <Link
          className={"join-item btn " + (pageNum === 1 ? "btn-disabled" : "")}
          to={`${pageURL}/1`}
        >
          <FontAwesomeIcon icon={faAnglesLeft} />
        </Link>
        {pageNum - 4 >= 1 && pageNum >= maxPageNum && (
          <Link className="join-item btn" to={`${pageURL}/${pageNum - 4}`}>
            {pageNum - 4}
          </Link>
        )}
        {pageNum - 3 >= 1 && pageNum >= maxPageNum - 1 && (
          <Link className="join-item btn" to={`${pageURL}/${pageNum - 3}`}>
            {pageNum - 3}
          </Link>
        )}
        {pageNum - 2 >= 1 && (
          <Link className="join-item btn" to={`${pageURL}/${pageNum - 2}`}>
            {pageNum - 2}
          </Link>
        )}
        {pageNum - 1 >= 1 && (
          <Link className="join-item btn" to={`${pageURL}/${pageNum - 1}`}>
            {pageNum - 1}
          </Link>
        )}
        <Link className="join-item btn btn-active" to={`${pageURL}/${pageNum}`}>
          {pageNum}
        </Link>
        {pageNum + 1 <= maxPageNum && (
          <Link className="join-item btn" to={`${pageURL}/${pageNum + 1}`}>
            {pageNum + 1}
          </Link>
        )}
        {pageNum + 2 <= maxPageNum && (
          <Link className="join-item btn" to={`${pageURL}/${pageNum + 2}`}>
            {pageNum + 2}
          </Link>
        )}
        {pageNum + 3 <= maxPageNum && pageNum <= 2 && (
          <Link className="join-item btn" to={`${pageURL}/${pageNum + 3}`}>
            {pageNum + 3}
          </Link>
        )}
        {pageNum + 4 <= maxPageNum && pageNum <= 1 && (
          <Link className="join-item btn" to={`${pageURL}/${pageNum + 4}`}>
            {pageNum + 4}
          </Link>
        )}
        <Link
          className={
            "join-item btn " + (pageNum === maxPageNum ? "btn-disabled" : "")
          }
          to={`${pageURL}/${maxPageNum}`}
        >
          <FontAwesomeIcon icon={faAnglesRight} />
        </Link>
      </div>
    </div>
  );
};

export default Pagination;
