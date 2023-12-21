import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faAnglesLeft, faAnglesRight } from "@fortawesome/free-solid-svg-icons";

const Pagination = ({ totalCount, pageNum, setPageNum, pageSize }) => {
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
        <button
          className={"join-item btn " + (pageNum === 1 ? "btn-disabled" : "")}
          onClick={() => setPageNum(1)}
        >
          <FontAwesomeIcon icon={faAnglesLeft} />
        </button>
        {pageNum - 4 >= 1 && pageNum >= maxPageNum && (
          <button
            className="join-item btn"
            onClick={() => setPageNum(pageNum - 4)}
          >
            {pageNum - 4}
          </button>
        )}
        {pageNum - 3 >= 1 && pageNum >= maxPageNum - 1 && (
          <button
            className="join-item btn"
            onClick={() => setPageNum(pageNum - 3)}
          >
            {pageNum - 3}
          </button>
        )}
        {pageNum - 2 >= 1 && (
          <button
            className="join-item btn"
            onClick={() => setPageNum(pageNum - 2)}
          >
            {pageNum - 2}
          </button>
        )}
        {pageNum - 1 >= 1 && (
          <button
            className="join-item btn"
            onClick={() => setPageNum(pageNum - 1)}
          >
            {pageNum - 1}
          </button>
        )}
        <button className="join-item btn btn-active">{pageNum}</button>
        {pageNum + 1 <= maxPageNum && (
          <button
            className="join-item btn"
            onClick={() => setPageNum(pageNum + 1)}
          >
            {pageNum + 1}
          </button>
        )}
        {pageNum + 2 <= maxPageNum && (
          <button
            className="join-item btn"
            onClick={() => setPageNum(pageNum + 2)}
          >
            {pageNum + 2}
          </button>
        )}
        {pageNum + 3 <= maxPageNum && pageNum <= 2 && (
          <button
            className="join-item btn"
            onClick={() => setPageNum(pageNum + 3)}
          >
            {pageNum + 3}
          </button>
        )}
        {pageNum + 4 <= maxPageNum && pageNum <= 1 && (
          <button
            className="join-item btn"
            onClick={() => setPageNum(pageNum + 4)}
          >
            {pageNum + 4}
          </button>
        )}
        <button
          className={
            "join-item btn " + (pageNum === maxPageNum ? "btn-disabled" : "")
          }
          onClick={() => setPageNum(maxPageNum)}
        >
          <FontAwesomeIcon icon={faAnglesRight} />
        </button>
      </div>
    </div>
  );
};

export default Pagination;
