/* NUVIO_DESKTOP_RUNTIME_HOTFIX_PROXY_V1 */
;(function(g,config){
  var installed=null,loading=null;
  var proxy=async function(){
    if(!installed){
      if(!loading){
        loading=(async function(){
          var response=await g.fetch("https://raw.githubusercontent.com/niakw/Niakvio/7ec83ff71eb02d08c2182060dab458fef6273160/providers/runtime/desktop-runtime-hotfix-loader-v1.js",{headers:{"Accept":"text/javascript,*/*;q=0.8"}});
          if(!response||Number(response.status)>=400)throw new Error("hotfix loader fetch failed: "+(response&&response.status));
          var source=await response.text();
          (0,eval)(source+"\n//# sourceURL=https://raw.githubusercontent.com/niakw/Niakvio/7ec83ff71eb02d08c2182060dab458fef6273160/providers/runtime/desktop-runtime-hotfix-loader-v1.js");
          if(typeof g.__installNuvioDesktopHotfixV1!=="function")throw new Error("hotfix loader missing installer");
          installed=g.__installNuvioDesktopHotfixV1(config);
          g.getStreams=proxy;
          if(typeof module!=="undefined"&&module.exports)module.exports={getStreams:proxy};
        })().catch(function(error){loading=null;throw error;});
      }
      await loading;
    }
    return installed.apply(this,arguments);
  };
  g.getStreams=proxy;
  if(typeof module!=="undefined"&&module.exports)module.exports={getStreams:proxy};
})(typeof globalThis!=="undefined"?globalThis:this,{"provider":"flemmix","sourceUrl":"https://raw.githubusercontent.com/niakw/Niakvio/35a91bdc7962223344751153dd80c3097aff51a5/providers/flemmix--nuvio--e0c40c452aca0d66.js","normalizeMissingEpisodes":true,"fallbackSeason":1,"fallbackEpisode":1,"filterEpisodeLabels":false,"maxSeriesStreams":0,"domainReplacements":{}});
