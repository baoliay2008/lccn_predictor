import ContestsUserNumStackedArea from "../../components/charts/ContestsUserNumStackedArea.jsx";
import useSWR from "swr";
import { baseUrl } from "../../data/constants.js";

const ContestsUserNum = () => {
  const { data: contests } = useSWR(
    `${baseUrl}/contests/user-num-last-ten`,
    (url) => fetch(url).then((r) => r.json()),
    { revalidateOnFocus: false }
  );
  return (
    contests && (
      <div className="container mx-auto text-center w-8/9">
        <ContestsUserNumStackedArea contests={contests} />
      </div>
    )
  );
};

export default ContestsUserNum;
