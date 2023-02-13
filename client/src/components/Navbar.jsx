import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faCheck,
  faHouse,
  faPalette,
  // faArrowUpRightDots,
  // faBoxArchive,
  // faCircleQuestion,
} from "@fortawesome/free-solid-svg-icons";
import { themes } from "../data/constants";
import { Link } from "react-router-dom";

const Theme = ({ dataTheme, setDataTheme }) => {
  return (
    <div className="dropdown dropdown-hover dropdown-bottom dropdown-end">
      <label tabIndex={0} className="btn m-1">
        <span className="hidden md:flex">Theme</span>
        <FontAwesomeIcon className="md:hidden" icon={faPalette} size="lg" />
      </label>
      <ul
        tabIndex={0}
        className="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-52"
      >
        {themes.map((t) => (
          <li
            key={t}
            onClick={() => setDataTheme(t)}
            className={t === dataTheme ? "bg-primary" : ""}
          >
            <div>
              {t}
              {t === dataTheme && <FontAwesomeIcon icon={faCheck} size="lg" />}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

const Navbar = ({ dataTheme, setDataTheme }) => {
  return (
    <div className="navbar bg-base-100">
      <div className="navbar-start">
        <Link to="/" className="btn m-1">
          <span className="hidden md:flex">Home</span>
          <FontAwesomeIcon className="md:hidden" icon={faHouse} size="lg" />
        </Link>
      </div>

      {/* <ul className="menu menu-horizontal bg-base-100 rounded-box navbar-center">
        <li>
          <Link className="active" to="/">
            <span className="hidden md:flex">Predicted</span>
            <FontAwesomeIcon className="md:hidden" icon={faArrowUpRightDots} size="lg" />
          </Link>
        </li>
        <li>
          <a>
          <span className="hidden md:flex">Archived</span>
            <FontAwesomeIcon className="md:hidden" icon={faBoxArchive} size="lg" />
          </a>
        </li>
        <li>
          <a>
          <span className="hidden md:flex">FAQ</span>
            <FontAwesomeIcon className="md:hidden" icon={faCircleQuestion} size="lg" />
          </a>
        </li>
      </ul> */}

      <div className="navbar-end">
        <Theme dataTheme={dataTheme} setDataTheme={setDataTheme} />
      </div>
    </div>
  );
};

export default Navbar;
