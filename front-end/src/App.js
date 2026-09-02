import { Suspense, lazy } from "react";
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

const Timeline = LazyWrapper(lazy(() => import("./pages/Timeline")));
const Home = LazyWrapper(lazy(() => import("./pages/Timeline/Home")));
const Top = LazyWrapper(lazy(() => import("./pages/Timeline/Top")));
const Random = LazyWrapper(lazy(() => import("./pages/Timeline/Random")));

// PUBLIC_URL is "" for root-hosted builds and carries the sub-path when the
// bundle is served from one (e.g. a GitHub Pages project site), so the routes
// keep working either way.
export default function App() {
  return (
    <Router basename={process.env.PUBLIC_URL}>
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
