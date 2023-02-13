import { useState, useEffect } from "react";

const useFetch = (
  url,
  method = "GET",
  headers = { "Content-Type": "text/plain" },
  body = null
) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const controller = new AbortController();
    const signal = controller.signal;

    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(url, {
          method,
          headers,
          body,
          signal,
        });
        const json = await response.json();
        setData(json);
      } catch (err) {
        if (err.name === "AbortError") {
          // Request was aborted, so do nothing
          console.log("fetch aborted");
          return;
        }
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    // Clean up function to abort the request if the component unmounts
    return () => controller.abort();
  }, [url, method, body]);

  return { data, loading, error };
};

export default useFetch;
