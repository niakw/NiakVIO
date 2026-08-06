/* NUVIO_DESKTOP_RUNTIME_HOTFIX_V1 */
;(function(g,config){
  if(!g)return;
  if(typeof g.global==="undefined")g.global=g;

  if(typeof g.setTimeout!=="function"){
    g.setTimeout=function(callback,delay){
      if((Number(delay)||0)<=0&&typeof callback==="function"&&typeof Promise!=="undefined"){
        Promise.resolve().then(callback).catch(function(){});
      }
      return 0;
    };
  }
  if(typeof g.clearTimeout!=="function")g.clearTimeout=function(){};
  if(typeof g.setInterval!=="function")g.setInterval=function(){return 0;};
  if(typeof g.clearInterval!=="function")g.clearInterval=function(){};

  if(config.domainReplacements&&typeof g.fetch==="function"){
    var state=g.__nuvioDesktopHotfixFetchV1;
    if(!state){
      state={native:g.fetch.bind(g),rules:Object.create(null)};
      g.__nuvioDesktopHotfixFetchV1=state;
      g.fetch=function(input,init){
        var next=input;
        try{
          var raw=(typeof Request!=="undefined"&&input instanceof Request)?input.url:String(input);
          var url=new URL(raw),replacement=state.rules[String(url.hostname).toLowerCase()];
          if(replacement){
            url.hostname=replacement;
            next=(typeof Request!=="undefined"&&input instanceof Request)?new Request(url.toString(),input):url.toString();
          }
        }catch(_error){}
        return state.native(next,init);
      };
    }
    Object.keys(config.domainReplacements).forEach(function(source){
      state.rules[String(source).toLowerCase()]=String(config.domainReplacements[source]).toLowerCase();
    });
  }

  function positive(value,fallback){
    var number=Number(value);
    return Number.isFinite(number)&&number>0?Math.floor(number):fallback;
  }
  function isSeries(type){
    var value=String(type||"").toLowerCase();
    return value==="tv"||value==="series"||value==="show";
  }
  function textOf(stream){
    if(!stream||typeof stream!=="object")return "";
    return [stream.name,stream.title,stream.description,stream.size,stream.url]
      .filter(function(value){return value!=null;}).join(" ");
  }
  function episodeMatch(stream,season,episode){
    var text=textOf(stream);
    if(!text)return false;
    var s=String(season),e=String(episode);
    var patterns=[
      new RegExp("S0*"+s+"\\s*E0*"+e,"i"),
      new RegExp("\\b0*"+s+"x0*"+e+"\\b","i"),
      new RegExp("saison\\s*0*"+s+"[^0-9]{0,16}(?:episode|ep)\\s*0*"+e,"i"),
      new RegExp("season\\s*0*"+s+"[^0-9]{0,16}(?:episode|ep)\\s*0*"+e,"i")
    ];
    for(var i=0;i<patterns.length;i++)if(patterns[i].test(text))return true;
    return false;
  }

  var original=null,loading=null;
  var wrapped=async function(tmdbId,mediaType,season,episode){
    var series=isSeries(mediaType);
    if(series&&config.normalizeMissingEpisodes){
      season=positive(season,config.fallbackSeason);
      episode=positive(episode,config.fallbackEpisode);
    }
    if(!original){
      if(!loading){
        loading=(async function(){
          var response=await g.fetch(config.sourceUrl,{headers:{"Accept":"text/javascript,*/*;q=0.8"}});
          if(!response||Number(response.status)>=400)throw new Error("hotfix source fetch failed: "+(response&&response.status));
          var source=await response.text();
          if(!source||source.length<32)throw new Error("hotfix source empty");
          var beforeGlobal=g.getStreams;
          (0,eval)(source+"\n//# sourceURL="+config.sourceUrl);
          var candidate=null;
          if(typeof g.getStreams==="function"&&g.getStreams!==wrapped&&g.getStreams!==beforeGlobal)candidate=g.getStreams;
          if(!candidate&&typeof module!=="undefined"&&module.exports&&typeof module.exports.getStreams==="function")candidate=module.exports.getStreams;
          if(!candidate&&g.__provider&&typeof g.__provider.getStreams==="function")candidate=g.__provider.getStreams;
          g.getStreams=wrapped;
          if(typeof module!=="undefined"&&module.exports)module.exports={getStreams:wrapped};
          if(!candidate)throw new Error("hotfix original getStreams missing");
          original=candidate;
          return candidate;
        })().catch(function(error){loading=null;throw error;});
      }
      await loading;
    }
    var result=await original.call(this,tmdbId,mediaType,season,episode);
    if(!series||!Array.isArray(result))return result;
    var output=result;
    if(config.filterEpisodeLabels){
      var exact=result.filter(function(stream){return episodeMatch(stream,season,episode);});
      if(exact.length)output=exact;
    }
    if(config.maxSeriesStreams>0&&output.length>config.maxSeriesStreams)output=output.slice(0,config.maxSeriesStreams);
    return output;
  };
  wrapped.__nuvioDesktopHotfixV1=true;
  g.getStreams=wrapped;
  if(typeof module!=="undefined"&&module.exports)module.exports={getStreams:wrapped};
})(typeof globalThis!=="undefined"?globalThis:this,{"provider":"coflix","sourceUrl":"https://raw.githubusercontent.com/niakw/Niakvio/35a91bdc7962223344751153dd80c3097aff51a5/providers/coflix--nuvio--48239f7b107a98b2.js","normalizeMissingEpisodes":true,"fallbackSeason":1,"fallbackEpisode":1,"filterEpisodeLabels":false,"maxSeriesStreams":0,"domainReplacements":{}});
