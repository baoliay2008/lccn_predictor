import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faCopyright, faPen } from "@fortawesome/free-solid-svg-icons";

const Footer = () => {
  return (
    <footer className="footer p-10 bg-neutral text-neutral-content">
      <div>
        <span className="footer-title">LCCN Predictor</span>
        <a
          href="https://twitter.com/intent/tweet?text=lccn.lbao.site%20Leetcode%20weekly%20and%20biweekly%20contest%20rating%20predictor"
          target="_blank"
          rel="noreferrer noopener"
        >
          <img
            src="https://img.shields.io/badge/share%20on-Twitter-blue"
            alt="share on twitter"
          />
        </a>
        <p>LeetCode weekly and biweekly contest rating predictor.</p>
        <p>
          Copyright <FontAwesomeIcon icon={faCopyright} /> 2022-2025 &nbsp;
          <FontAwesomeIcon icon={faPen} /> L. Bao.
        </p>
      </div>
      {/* <div>
        <span className="footer-title">Official Sites</span>
        <a
          className="text-secondary"
          href="https://leetcode.cn/contest"
          target="_blank"
          rel="noreferrer noopener"
        >
          LCCN
        </a>
        <a
          className="text-accent"
          href="https://leetcode.com/contest"
          target="_blank"
          rel="noreferrer noopener"
        >
          LCUS
        </a>
      </div> */}
      <div>
        <span className="footer-title">Github Repo</span>
        <a
          target="_blank"
          rel="noreferrer noopener"
          href="https://github.com/baoliay2008/lccn_predictor/blob/main/LICENSE"
        >
          <img
            src="https://img.shields.io/github/license/baoliay2008/lccn_predictor"
            alt="License"
          />
        </a>
        <a
          target="_blank"
          rel="noreferrer noopener"
          href="https://github.com/baoliay2008/lccn_predictor/issues"
        >
          <img
            src="https://img.shields.io/github/issues/baoliay2008/lccn_predictor"
            alt="Issues"
          />
        </a>
        <a
          target="_blank"
          rel="noreferrer noopener"
          href="https://github.com/baoliay2008/lccn_predictor/pulls"
        >
          <img
            src="https://img.shields.io/github/issues-pr/baoliay2008/lccn_predictor"
            alt="Pull Requests"
          />
        </a>
        <a
          target="_blank"
          rel="noreferrer noopener"
          href="https://github.com/baoliay2008/lccn_predictor/commits/main"
        >
          <img
            src="https://img.shields.io/github/last-commit/baoliay2008/lccn_predictor"
            alt="Last Commit"
          />
        </a>
      </div>
    </footer>
  );
};

export default Footer;
