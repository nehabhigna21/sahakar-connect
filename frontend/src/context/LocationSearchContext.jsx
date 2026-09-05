import { createContext, useContext, useState } from "react";

const LocationSearchContext = createContext(null);

export function LocationSearchProvider({ children }) {
  const [zone, setZone] = useState(() => localStorage.getItem("zone") || "Zone-1");
  const [search, setSearch] = useState("");

  function updateZone(next) {
    setZone(next);
    localStorage.setItem("zone", next);
  }

  return (
    <LocationSearchContext.Provider value={{ zone, setZone: updateZone, search, setSearch }}>
      {children}
    </LocationSearchContext.Provider>
  );
}

export function useLocationSearch() {
  return useContext(LocationSearchContext);
}
