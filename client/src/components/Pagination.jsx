import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faAnglesLeft, faAnglesRight } from "@fortawesome/free-solid-svg-icons";
import { Link } from "react-router-dom";

const Pagination = ({ totalCount, pageNum, pageSize, titleSlug }) => {
  const maxPageNum = Math.ceil(totalCount / pageSize);
  return (
    <div
      className="container mx-auto text-center"
      style={{
        marginTop: "0.5em",
        marginBottom: "1.0em",
      }}
    >
      <div className="btn-group">
        <Link
          to={`/predicted/${titleSlug}/1`}
          className={"btn " + (pageNum === 1 ? "btn-disabled" : "")}
        >
          <FontAwesomeIcon icon={faAnglesLeft} />
        </Link>
        {pageNum - 4 >= 1 && pageNum >= maxPageNum && (
          <Link to={`/predicted/${titleSlug}/${pageNum - 4}`} className="btn">
            {pageNum - 4}
          </Link>
        )}
        {pageNum - 3 >= 1 && pageNum >= maxPageNum - 1 && (
          <Link to={`/predicted/${titleSlug}/${pageNum - 3}`} className="btn">
            {pageNum - 3}
          </Link>
        )}
        {pageNum - 2 >= 1 && (
          <Link to={`/predicted/${titleSlug}/${pageNum - 2}`} className="btn">
            {pageNum - 2}
          </Link>
        )}
        {pageNum - 1 >= 1 && (
          <Link to={`/predicted/${titleSlug}/${pageNum - 1}`} className="btn">
            {pageNum - 1}
          </Link>
        )}
        <button className="btn btn-active">{pageNum}</button>
        {pageNum + 1 <= maxPageNum && (
          <Link to={`/predicted/${titleSlug}/${pageNum + 1}`} className="btn">
            {pageNum + 1}
          </Link>
        )}
        {pageNum + 2 <= maxPageNum && (
          <Link to={`/predicted/${titleSlug}/${pageNum + 2}`} className="btn">
            {pageNum + 2}
          </Link>
        )}
        {pageNum + 3 <= maxPageNum && pageNum <= 2 && (
          <Link to={`/predicted/${titleSlug}/${pageNum + 3}`} className="btn">
            {pageNum + 3}
          </Link>
        )}
        {pageNum + 4 <= maxPageNum && pageNum <= 1 && (
          <Link to={`/predicted/${titleSlug}/${pageNum + 4}`} className="btn">
            {pageNum + 4}
          </Link>
        )}
        <Link to={`/predicted/${titleSlug}/${maxPageNum}`}
          className={"btn " + (pageNum === maxPageNum ? "btn-disabled" : "")}
        >
          <FontAwesomeIcon icon={faAnglesRight} />
        </Link>
      </div>
    </div>
  );
};

export default Pagination;
