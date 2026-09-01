import { useEffect, useState } from "react";
import countries from "@countrystatecity/countries-browser/data/countries.json";
import PremiumCombobox from "./PremiumCombobox";

let geography;
async function api(){geography ||= import("@countrystatecity/countries-browser");return geography}

export function CountryCombobox({value,onChange,label="Country"}){return <PremiumCombobox label={label} value={value} onChange={onChange} options={countries} allowCustom placeholder="Search countries" getLabel={x=>typeof x==="string"?x:`${x.emoji||""} ${x.name}`} getKey={x=>typeof x==="string"?x:x.iso2}/>}

export function StateCombobox({country,value,onChange}){const [options,setOptions]=useState([]);const [loading,setLoading]=useState(false);useEffect(()=>{setOptions([]);onChange(null);if(!country?.iso2)return;setLoading(true);api().then(x=>x.getStatesOfCountry(country.iso2)).then(setOptions).catch(()=>setOptions([])).finally(()=>setLoading(false))},[country?.iso2]);if(!country?.iso2||(!loading&&!options.length))return null;return <PremiumCombobox label="State / Province" value={value} onChange={onChange} options={options} loading={loading} placeholder="Search states or provinces" getLabel={x=>x.name} getKey={x=>x.iso2}/>}

export function CityCombobox({country,state,value,onChange}){const [options,setOptions]=useState([]);const [loading,setLoading]=useState(false);const [error,setError]=useState("");useEffect(()=>{setOptions([]);setError("");if(!country?.iso2||!state?.iso2)return;setLoading(true);api().then(x=>x.getCitiesOfState(country.iso2,state.iso2)).then(setOptions).catch(()=>setError("Unable to load cities. Enter your city manually.")).finally(()=>setLoading(false))},[country?.iso2,state?.iso2]);return <PremiumCombobox label="City" value={value} onChange={onChange} options={options} disabled={!country} loading={loading} error={error} allowCustom placeholder={country?(state?"Search cities":"Enter city manually or select a state"):"Select a country first"} getLabel={x=>typeof x==="string"?x:x.name} getKey={x=>typeof x==="string"?x:x.id}/>}

export function LocationCombobox({country,setCountry,state,setState,city,setCity}){return <div className="location-fields"><CountryCombobox value={country} onChange={x=>{setCountry(x);setCity(null)}}/><StateCombobox country={country} value={state} onChange={setState}/><CityCombobox country={country} state={state} value={city} onChange={setCity}/></div>}
