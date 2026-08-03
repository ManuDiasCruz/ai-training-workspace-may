import { Suspense, lazy, Component } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route
} from "react-router-dom";

const Loading = () => (
  <div>Loading...</div>
  );
  
const LazyWrapper = (Component) => (props) => (
  <Suspense fallback={<Loading />}>
    <Component {...props} />
  </Suspense>
)

// PUBLIC_URL may be '', a path ('/my-app') or a full URL; the router only wants the path part
const basename = process.env.PUBLIC_URL
  ? new URL(process.env.PUBLIC_URL, window.location.origin).pathname
  : "/";

const Timeline = LazyWrapper(lazy(() => import("./pages/Timeline")));
const Home = LazyWrapper(lazy(() => import("./pages/Timeline/Home")));
const Top = LazyWrapper(lazy(() => import("./pages/Timeline/Top")));
const Random = LazyWrapper(lazy(() => import("./pages/Timeline/Random")));

export default function App() {
  return (
    <Router basename={basename}>
      <Routes>
        <Route path="/" element={<Timeline />}>
          <Route path="/" element={<Home />} />
          <Route path="/top" element={<Top />} />
          <Route path="/random" element={<Random />} />
          <Route path="*" element={<div>Not found!</div>} />
        </Route>
      </Routes>
    </Router>
  )
}
