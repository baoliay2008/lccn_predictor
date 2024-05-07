import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faCheck, faHouse, faPalette } from "@fortawesome/free-solid-svg-icons";
import { themes } from "../data/constants";
import { DataThemeContext } from "../App";
import { Link } from "react-router-dom";
import { useContext, useState } from "react";

const ThemeButton = () => {
  const { dataTheme, setDataTheme } = useContext(DataThemeContext);
  const [showThemeList, setShowThemeList] = useState(false);

  return (
    <div className="dropdown dropdown-end">
      <label className="btn m-1" tabIndex={0} onClick={() => setShowThemeList(!showThemeList)}>
        <span className="hidden md:flex">Theme</span>
        <FontAwesomeIcon className="md:hidden" icon={faPalette} size="lg" />
      </label>

      {showThemeList &&
        <ul tabIndex={0} onBlur={() => setShowThemeList(false)}
          className="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-44 theme-list-scrollbar 
          block max-h-[400px] overflow-y-auto"
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
        </ul>}
    </div>
  );
};

const Navbar = () => {
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
        <ThemeButton />
      </div>
    </div>
  );
};

export default Navbar;
