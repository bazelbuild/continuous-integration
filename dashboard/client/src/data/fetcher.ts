export default function fetcher(input: RequestInfo, init?: RequestInit) {
  return fetch(input, init).then((res) => res.json());
}
