export default function fetcher(input: RequestInfo, init?: RequestInit) {
  return fetch(input, init).then((res) => {
    if (res.ok) {
      return res.json();
    }

    return res.json().then((error) => {
      throw error;
    });
  });
}
