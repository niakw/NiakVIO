
/* NUVIO_PROVIDER_SECURITY_HARDENING_V1:36ae804b950d */
function __nuvioDecodeUtf8PercentBytes(value){
  var input=String(value==null?"":value),bytes=[],i=0,hex;
  while(i<input.length){
    if(input.charAt(i)!=="%"||i+2>=input.length||!/^[0-9a-fA-F]{2}$/.test(hex=input.slice(i+1,i+3)))throw new URIError("URI malformed");
    bytes.push(parseInt(hex,16));i+=3;
  }
  var out="",p=0;
  function cont(v){return v>=128&&v<=191}
  while(p<bytes.length){
    var b0=bytes[p++],b1,b2,b3,cp;
    if(b0<=127){out+=String.fromCharCode(b0);continue}
    if(b0>=194&&b0<=223){
      if(p>=bytes.length||!cont(b1=bytes[p++]))throw new URIError("URI malformed");
      cp=((b0&31)<<6)|(b1&63);out+=String.fromCharCode(cp);continue;
    }
    if(b0>=224&&b0<=239){
      if(p+1>=bytes.length||!cont(b1=bytes[p++])||!cont(b2=bytes[p++]))throw new URIError("URI malformed");
      if((b0===224&&b1<160)||(b0===237&&b1>159))throw new URIError("URI malformed");
      cp=((b0&15)<<12)|((b1&63)<<6)|(b2&63);out+=String.fromCharCode(cp);continue;
    }
    if(b0>=240&&b0<=244){
      if(p+2>=bytes.length||!cont(b1=bytes[p++])||!cont(b2=bytes[p++])||!cont(b3=bytes[p++]))throw new URIError("URI malformed");
      if((b0===240&&b1<144)||(b0===244&&b1>143))throw new URIError("URI malformed");
      cp=((b0&7)<<18)|((b1&63)<<12)|((b2&63)<<6)|(b3&63);cp-=65536;
      out+=String.fromCharCode(55296+(cp>>10),56320+(cp&1023));continue;
    }
    throw new URIError("URI malformed");
  }
  return out;
}
var __nuvioProviderSilentLog=function(){};
/* NUVIO_PROVIDER_CONSOLE_SHADOW_V1 */
var console={
  log:__nuvioProviderSilentLog,warn:__nuvioProviderSilentLog,
  error:__nuvioProviderSilentLog,info:__nuvioProviderSilentLog,
  debug:__nuvioProviderSilentLog,trace:__nuvioProviderSilentLog,
  dir:__nuvioProviderSilentLog
};
var _0x281d9e=_0xc337;(function(_0x409329,_0x2141cb){var _0xab6af5={_0x3db0f7:0x17d,_0x4746bb:0x1d3,_0x495b10:0x1cf,_0x1091c6:0x1ba,_0x4cc3af:0x202},_0x6aeff0=_0xc337,_0x25e406=_0x409329();while(!![]){try{var _0x45485f=-parseInt(_0x6aeff0(_0xab6af5._0x3db0f7))/0x1*(parseInt(_0x6aeff0(_0xab6af5._0x4746bb))/0x2)+parseInt(_0x6aeff0(0x1e8))/0x3+parseInt(_0x6aeff0(0x1b1))/0x4*(parseInt(_0x6aeff0(_0xab6af5._0x495b10))/0x5)+-parseInt(_0x6aeff0(_0xab6af5._0x1091c6))/0x6+parseInt(_0x6aeff0(0x192))/0x7+-parseInt(_0x6aeff0(0x1bf))/0x8+parseInt(_0x6aeff0(_0xab6af5._0x4cc3af))/0x9;if(_0x45485f===_0x2141cb)break;else _0x25e406['push'](_0x25e406['shift']());}catch(_0x1d6af7){_0x25e406['push'](_0x25e406['shift']());}}}(_0x50b3,0xbff13));var __async=(_0x46023d,_0x3e28e4,_0x2fb2cf)=>{return new Promise((_0x4fa95a,_0x422774)=>{var _0x25c329=_0xc337,_0x4848d7=_0xcfeeea=>{var _0x3e3172=_0xc337;try{_0x5a2533(_0x2fb2cf[_0x3e3172(0x189)](_0xcfeeea));}catch(_0x4a4f65){_0x422774(_0x4a4f65);}},_0x7029e6=_0x3564e4=>{try{_0x5a2533(_0x2fb2cf['throw'](_0x3564e4));}catch(_0x32bacf){_0x422774(_0x32bacf);}},_0x5a2533=_0x473cf4=>_0x473cf4[_0x25c329(0x19a)]?_0x4fa95a(_0x473cf4[_0x25c329(0x17b)]):Promise[_0x25c329(0x1cd)](_0x473cf4['value'])[_0x25c329(0x18d)](_0x4848d7,_0x7029e6);_0x5a2533((_0x2fb2cf=_0x2fb2cf['apply'](_0x46023d,_0x3e28e4))[_0x25c329(0x189)]());});},PROVIDER_NAME=_0x281d9e(0x1d1),TMDB_API_KEY=_0x281d9e(0x1c8),TMDB_BASE=_0x281d9e(0x1c3),MAX_RESULTS_MOVIE=0x5,MAX_RESULTS_EPISODE=0x2,WORKER_DOMAINS=[_0x281d9e(0x1f7),_0x281d9e(0x19d)],MOBILE_UAS=['Mozilla/5.0\x20(Windows\x20NT\x2010.0;\x20Win64;\x20x64)\x20AppleWebKit/537.36\x20(KHTML,\x20like\x20Gecko)\x20Chrome/120.0.0.0\x20Safari/537.36','Mozilla/5.0\x20(Linux;\x20Android\x2014;\x20Pixel\x208\x20Pro)\x20AppleWebKit/537.36\x20(KHTML,\x20like\x20Gecko)\x20Chrome/124.0.0.0\x20Mobile\x20Safari/537.36','Mozilla/5.0\x20(iPhone;\x20CPU\x20iPhone\x20OS\x2017_0\x20like\x20Mac\x20OS\x20X)\x20AppleWebKit/605.1.15\x20(KHTML,\x20like\x20Gecko)\x20Version/17.0\x20Mobile/15E148\x20Safari/604.1'];function getInvertedSortTag(_0x2b0846,_0x58e8dd){var _0x574189={_0x4f7471:0x18b,_0x4a60f5:0x191},_0x4229d1=_0x281d9e;_0x58e8dd===void 0x0&&(_0x58e8dd=0xf423f);var _0x3d274b=Math['max'](0x0,parseInt(_0x2b0846,0xa)||0x0),_0x4d656f=Math[_0x4229d1(_0x574189._0x4f7471)](0x0,_0x58e8dd-_0x3d274b),_0x103bbe=_0x4d656f[_0x4229d1(_0x574189._0x4a60f5)](0x2)['padStart'](0x14,'0');return _0x103bbe[_0x4229d1(0x1bd)]('')[_0x4229d1(0x1bc)](function(_0x1fa5a8){return _0x1fa5a8==='1'?'\ufeff':'​';})['join']('');}function resolveSettings(_0x2c8d8b){var _0x372398={_0x371298:0x164,_0x3924c9:0x1f5,_0xce8c50:0x1b7,_0x413f7d:0x1be,_0x197142:0x203},_0x51264a=_0x281d9e,_0x26d0f7={'sortBy':'quality'};try{var _0x52197f=_0x2c8d8b;!_0x52197f&&typeof globalThis!==_0x51264a(0x1a9)&&(_0x52197f=globalThis[_0x51264a(_0x372398._0x371298)]||globalThis['SETTINGS']||globalThis[_0x51264a(_0x372398._0x3924c9)]);!_0x52197f&&typeof global!=='undefined'&&(_0x52197f=global['SCRAPER_SETTINGS']||global[_0x51264a(_0x372398._0xce8c50)]||global['settings']);!_0x52197f&&typeof window!=='undefined'&&(_0x52197f=window[_0x51264a(0x164)]||window[_0x51264a(0x1b7)]||window['settings']);if(_0x52197f){var _0x4cf5d8=_0x52197f[_0x51264a(0x203)]||_0x52197f['sort_by']||_0x52197f['sort']||'';typeof _0x4cf5d8===_0x51264a(0x18c)&&_0x4cf5d8!==null&&(_0x4cf5d8=_0x4cf5d8['value']||_0x4cf5d8['label']||'');var _0x411951=String(_0x4cf5d8)['toLowerCase']();_0x411951[_0x51264a(_0x372398._0x413f7d)](_0x51264a(0x19e))||_0x411951[_0x51264a(0x1be)]('largest')?_0x26d0f7['sortBy']='size':_0x26d0f7[_0x51264a(_0x372398._0x197142)]='quality';}}catch(_0xf8b270){console[_0x51264a(0x1a1)]('['+PROVIDER_NAME+_0x51264a(0x1de),_0xf8b270);}return _0x26d0f7;}function onSettings(){var _0x497ea4={_0x2e7ef0:0x1c0},_0x4730ce=_0x281d9e;return[{'type':'select','key':_0x4730ce(0x203),'name':_0x4730ce(_0x497ea4._0x2e7ef0),'label':'Sort\x20By','options':[{'label':'Quality\x20Score','value':'quality'},{'label':'Largest\x20Size','value':_0x4730ce(0x19e)}],'default':'quality'}];}function _0xc337(_0x466efc,_0x1b595f){_0x466efc=_0x466efc-0x15d;var _0x50b310=_0x50b3();var _0xc337b5=_0x50b310[_0x466efc];if(_0xc337['yVwkBV']===undefined){var _0x354406=function(_0x1df3f1){var _0x19866a='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=';var _0x46023d='',_0x3e28e4='';for(var _0x2fb2cf=0x0,_0x4fa95a,_0x422774,_0x4848d7=0x0;_0x422774=_0x1df3f1['charAt'](_0x4848d7++);~_0x422774&&(_0x4fa95a=_0x2fb2cf%0x4?_0x4fa95a*0x40+_0x422774:_0x422774,_0x2fb2cf++%0x4)?_0x46023d+=String['fromCharCode'](0xff&_0x4fa95a>>(-0x2*_0x2fb2cf&0x6)):0x0){_0x422774=_0x19866a['indexOf'](_0x422774);}for(var _0x7029e6=0x0,_0x5a2533=_0x46023d['length'];_0x7029e6<_0x5a2533;_0x7029e6++){_0x3e28e4+='%'+('00'+_0x46023d['charCodeAt'](_0x7029e6)['toString'](0x10))['slice'](-0x2);}return __nuvioDecodeUtf8PercentBytes(_0x3e28e4);};_0xc337['GCQSPT']=_0x354406,_0xc337['jXUBiu']={},_0xc337['yVwkBV']=!![];}var _0x2afd8f=_0x50b310[0x0],_0x41cbaf=_0x466efc+_0x2afd8f,_0x408615=_0xc337['jXUBiu'][_0x41cbaf];return!_0x408615?(_0xc337b5=_0xc337['GCQSPT'](_0xc337b5),_0xc337['jXUBiu'][_0x41cbaf]=_0xc337b5):_0xc337b5=_0x408615,_0xc337b5;}function getQualityRank(_0x3fb0db){var _0x2d48b7={_0x48a582:0x1ca,_0x252c07:0x1a5,_0x4fac3c:0x1be},_0x2a48f2=_0x281d9e,_0x8d3bb5=String(_0x3fb0db)[_0x2a48f2(0x1f8)]();if(_0x8d3bb5['includes'](_0x2a48f2(_0x2d48b7._0x48a582))||_0x8d3bb5[_0x2a48f2(0x1be)]('4k')||_0x8d3bb5['includes'](_0x2a48f2(_0x2d48b7._0x252c07)))return 0x4;if(_0x8d3bb5[_0x2a48f2(0x1be)]('1080')||_0x8d3bb5['includes']('fullhd')||_0x8d3bb5[_0x2a48f2(_0x2d48b7._0x4fac3c)](_0x2a48f2(0x176)))return 0x3;if(_0x8d3bb5[_0x2a48f2(0x1be)]('720')||_0x8d3bb5['includes']('hd'))return 0x2;if(_0x8d3bb5['includes']('480')||_0x8d3bb5['includes']('sd')||_0x8d3bb5['includes']('dvdrip'))return 0x1;return 0x0;}function removeAccents(_0x5c4945){return(_0x5c4945||'')['normalize']('NFKD')['replace'](/[\u0300-\u036f]/g,'');}function normalizeForCompare(_0x4cea8f){if(!_0x4cea8f)return'';var _0x200dc7=removeAccents(String(_0x4cea8f))['toLowerCase']();return _0x200dc7['replace'](/[^a-z0-9]/g,'');}function parseQuality(_0x462b4e){var _0xb9686b={_0x23dd37:0x1a5,_0x4d755e:0x1be,_0xe96ff9:0x174,_0x465c41:0x16b,_0x3e5794:0x1be,_0x16d83d:0x1ed,_0x55fc28:0x174},_0x5113b6=_0x281d9e,_0x54aa36=String(_0x462b4e||'')['toLowerCase']();if(_0x54aa36[_0x5113b6(0x1be)]('2160p')||_0x54aa36['includes']('4k')||_0x54aa36[_0x5113b6(0x1be)](_0x5113b6(_0xb9686b._0x23dd37)))return'2160p';if(_0x54aa36[_0x5113b6(_0xb9686b._0x4d755e)](_0x5113b6(_0xb9686b._0xe96ff9))||_0x54aa36[_0x5113b6(0x1be)](_0x5113b6(_0xb9686b._0x465c41))||_0x54aa36['includes']('full\x20hd'))return _0x5113b6(_0xb9686b._0xe96ff9);if(_0x54aa36[_0x5113b6(_0xb9686b._0x3e5794)]('720p'))return _0x5113b6(0x1c2);if([_0x5113b6(0x179),'sd',_0x5113b6(0x1ce),_0x5113b6(_0xb9686b._0x16d83d)][_0x5113b6(0x1d2)](function(_0xc628ee){var _0x5cc1f7=_0x5113b6;return _0x54aa36[_0x5cc1f7(0x1be)](_0xc628ee);}))return'480p';return _0x5113b6(_0xb9686b._0x55fc28);}function formatSize(_0x40579d){var _0x42a6df={_0x117d32:0x167,_0xecbbc7:0x167},_0x35119f=_0x281d9e;try{var _0x37152e=Number(_0x40579d);if(!_0x37152e||isNaN(_0x37152e))return'N/A';if(_0x37152e<0x400)return _0x37152e+'\x20B';if(_0x37152e<0x400*0x400)return(_0x37152e/0x400)[_0x35119f(_0x42a6df._0x117d32)](0x2)+'\x20KB';if(_0x37152e<0x400*0x400*0x400)return(_0x37152e/(0x400*0x400))[_0x35119f(_0x42a6df._0xecbbc7)](0x2)+_0x35119f(0x177);return(_0x37152e/(0x400*0x400*0x400))[_0x35119f(0x167)](0x2)+_0x35119f(0x16d);}catch(_0x1467a1){return'N/A';}}function escapeRegExp(_0x18ffff){return _0x18ffff['replace'](/[.*+?^${}()|[\]\\]/g,'\x5c$&');}function pad(_0x39dc6e,_0x3edaba){var _0x52da62={_0x432259:0x1e2},_0xb0b93a=_0x281d9e;return String(_0x39dc6e)[_0xb0b93a(_0x52da62._0x432259)](_0x3edaba,'0');}function decodeEntities(_0x19694f){var _0x1fb6f8={_0xa26ddd:0x1eb},_0x21d89a=_0x281d9e;if(!_0x19694f)return'';var _0x44a31e=/&(nbsp|amp|quot|lt|gt|#038);/g,_0x3ac9e7={'nbsp':'\x20','amp':'&','quot':'\x22','lt':'<','gt':'>','#038':'&'};return _0x19694f[_0x21d89a(_0x1fb6f8._0xa26ddd)](_0x44a31e,function(_0x45376b,_0xd48192){return _0x3ac9e7[_0xd48192];})['replace'](/&#(\d+);/g,function(_0x5f03e2,_0x4ca1a2){var _0x6e5d2b=_0x21d89a;return String[_0x6e5d2b(0x19b)](_0x4ca1a2);});}function getAnimeSearchPatterns(_0x202ab6,_0x2f9652){var _0x2684a3={_0x4242d6:0x1fa},_0xb912c2={},_0x3a7e1b=[];function _0x2196cd(_0x587026,_0x1c4029){var _0xa1c57e=_0xc337,_0x470414=_0x587026+':'+_0x1c4029;!_0xb912c2[_0x470414]&&(_0xb912c2[_0x470414]=!![],_0x3a7e1b[_0xa1c57e(_0x2684a3._0x4242d6)]([_0x587026,_0x1c4029]));}return _0x2196cd(_0x202ab6,_0x2f9652),_0x202ab6===0x1&&_0x2f9652>0xb&&[0xc,0xd]['forEach'](function(_0x3116ed){if(_0x2f9652>_0x3116ed)_0x2196cd(0x2,_0x2f9652-_0x3116ed);}),_0x3a7e1b;}function getAnimeSearchCodes(_0x2effbb,_0x4ae7b9){var _0x29454d={_0xaa009d:0x1fa},_0x5a4201=getAnimeSearchPatterns(_0x2effbb,_0x4ae7b9),_0x1a1099={},_0x4555c0=[];function _0x28d6f2(_0x3935fd){var _0xb3026d=_0xc337;!_0x1a1099[_0x3935fd]&&(_0x1a1099[_0x3935fd]=!![],_0x4555c0[_0xb3026d(_0x29454d._0xaa009d)](_0x3935fd));}return _0x5a4201['forEach'](function(_0x1708f4){var _0x1e51e2=_0x1708f4[0x0],_0x441442=_0x1708f4[0x1];_0x28d6f2('S'+pad(_0x1e51e2,0x2)+'E'+pad(_0x441442,0x2)),_0x28d6f2(pad(_0x1e51e2,0x2)+'x'+pad(_0x441442,0x2)),_0x28d6f2(_0x1e51e2+'.'+pad(_0x441442,0x2)),_0x1e51e2===0x1&&_0x441442!==0x1&&(_0x28d6f2(pad(_0x441442,0x2)),_0x28d6f2(pad(_0x441442,0x3)),_0x28d6f2('ep'+pad(_0x441442,0x2)),_0x28d6f2('e'+pad(_0x441442,0x2)));}),_0x4555c0;}var TITLE_END_RE=new RegExp('^(?:s\x5cd{1,2}e\x5cd{1,2}|\x5c[?\x5cd{3,4}p\x5c]?|(?:19|20)\x5cd{2}|ep?\x5cs*\x5cd+|episode\x5cs*\x5cd+|\x5c[(?:dual|dub|leg|sub|pt[\x5c-.]br|bluray|bdrip|webrip|web[\x5c-.]dl|hdtv|x264|x265|hevc|aac|mkv|mp4|avi|wmv|mov)\x5c]|(?:dual|dub|leg|sub|pt[\x5c-.]br|bluray|bdrip|webrip|web[\x5c-.]dl|hdtv|x264|x265|hevc|aac|mkv|mp4|avi|wmv|mov)|\x5c[\x5cd+|\x5cs-\x5cs\x5cd+)','i'),IGNORABLE_PREFIX_WORDS={'the':0x1,'a':0x1,'an':0x1,'o':0x1,'os':0x1,'as':0x1,'de':0x1,'do':0x1,'da':0x1,'dos':0x1,'das':0x1,'em':0x1,'no':0x1,'na':0x1,'nos':0x1,'nas':0x1,'um':0x1,'uma':0x1},NOISE_WORD_RE=new RegExp('^(?:\x5cd{4}|[a-z0-9]+(?:p|k)|bluray|bdrip|webrip|web|hdtv|x264|x265|hevc|aac|mkv|mp4|avi|wmv|mov|hdr|sdr|remux|dual|dub|dublado|leg|legendado|sub|pt[\x5c-.]?br|nf|netflix|hbo|max|hbomax|disney|disneyplus|amazon|prime|paramount|peacock|hulu|apple|appletv|star|globoplay|telecine|crunchyroll|funimation|youtube|vix|pluto|copia|copy|sample|extras?)$','i');function fetchPlain(_0x2c1e72,_0x3855f1){return __async(this,null,function*(){return fetch(_0x2c1e72,_0x3855f1||{});});}function fetchJson(_0x410bae,_0x33db9f){return __async(this,null,function*(){try{var _0x200b0a=yield fetchPlain(_0x410bae,{'headers':{'User-Agent':_0x33db9f}});if(!_0x200b0a['ok'])return null;return yield _0x200b0a['json']();}catch(_0x5619a4){return null;}});}function fetchTmdbDetails(_0x3ac9cd,_0x16df31,_0x594499){return __async(this,null,function*(){var _0x40f5e8=_0xc337,_0x4e670b=_0x16df31==='movie'?'/movie/'+_0x3ac9cd:_0x40f5e8(0x1a7)+_0x3ac9cd,_0x247b74=TMDB_BASE+_0x4e670b+'?api_key='+TMDB_API_KEY+'&language=en-US';return yield fetchJson(_0x247b74,_0x594499);});}function computeAbsoluteEpisode(_0x1526dd,_0x13a981,_0x2af2d6){var _0x34ad96={_0x34b65f:0x1df},_0x411bfe=_0x281d9e;if(!Array['isArray'](_0x1526dd))return null;var _0xd085ba=_0x2af2d6;for(var _0x1558f3=0x0;_0x1558f3<_0x1526dd[_0x411bfe(_0x34ad96._0x34b65f)];_0x1558f3++){var _0x339892=_0x1526dd[_0x1558f3];_0x339892['season_number']>0x0&&_0x339892['season_number']<_0x13a981&&(_0xd085ba+=_0x339892['episode_count']||0x0);}return _0xd085ba;}function _0x50b3(){var _0x18b3b8=['C2XPy2u','req1lJe','CM9TywPPx3rPDgXL','zNvSBgHK','z2v0','ieDc','z2v0u3rYzwfTCW','y2XLyw4','DgvZDa','BgLUAW','Aw5KzxHpzG','zgf0yq','mta4mha','ksbVBIa','zMHK','ie1c','Bw92Awu','zhzKCMLW','AxngAw5PDgu','DMfSDwu','C2L6zuLUtui','nZGYn05JCePcDa','v0vcuMLW','zMLSDgvY','rerqns4X','ug9YDhvNDwvZzsdWN4EN8j+hTW','C2vZC2LVBLvb','lZe6C2vHCMnO','C3rYAw5NAwz5','8j+nVYa','x2LZqw5PBwu','Agv2yW','C2v0','BMv4Da','x3bYB2nLC3nszxn1BhrZ','Bwf4','B2jQzwn0','DgHLBG','yw5PBwv6zxKXnJa4mJaYmY5HBMLTzxPLEte2mdGYmdiZlNDVCMTLCNmUzgv2','Dgv4Da','kI8Q','Dg9tDhjPBMC','nZKWnJu3mhPxsgXTvq','tI9b','x21HDgnOzxntzxjPzxnjBKzPBgvUyw1L','zMLSzq','ChjVDg90ExbL','DgHLia','kd8HxgqP','x2j1AwXKrg93BMXVywrmAw5R','zg9Uzq','zNjVBunOyxjdB2rL','x2DLBMvYyxrLtw92AwvrDwvYAwvZ','ms5HBMLTzxPLEwrSlNDVCMTLCNmUzgv2','C2L6zq','B3jPz2LUywXuAxrSzq','B3jPz2LUywXFDgL0Bgu','zxjYB3i','DhjPBq','sc4YnJq','mtbcAxq','DwHK','mJaYnG','l3r2lW','EwvHCG','Dw5KzwzPBMvK','CxvHBgL0Eq','BwvKAwfuExbL','rhvHBc1bDwrPBW','x3rPDgXLtwf0y2G','sersmta','y3vYCMvUDerVBwfPBKLUzgv4','zxzLCNK','mtKYt3DVuuPP','sc4YnJu','C3rHDhvZ','zMLSzxm','u2LUz2XLief1zgLV','8j+mJsa','u0vuveLor1m','sersmtaR','tva0','nJKXmZCYmMfisgH5EG','Edi2nq','BwfW','C3bSAxq','Aw5JBhvKzxm','mtaYmtK2ntz3qLjiAhK','C29YDf9IEq','Ahr0Chm6lY8','nZiWCa','Ahr0Chm6lY9HCgKUDgHLBw92AwvKyI5VCMCVmW','ue9tva','zg93BMXVywreB21HAw4','x3nLyxjJAe1VDMLLCW','rw5NBgLZAcdWN4E68j+hUcdIGkiGug9YDhvNDwvZzsdWN4EN8j+hTW','ndm5yZq3oge3nZfMmZvJmduWmJjMowzLywjJy2eWmwm','yMfZzurVBwfPBNm','mJe2ma','Bwf0y2G','ihWG8j+sVIa','CMvZB2X2zq','ndGWCa','mtmYmtmWsgDLAKnJ','CxvHBgL0EvjHBMS','qw5PBwvAzvK','C29Tzq','mtK2C0fHvvbL','zg90C1jHDW','yt12Awv3','x2v4DhjHy3rqBgf5zxjvCMW','ug9YDhvNDwvZzsdWN4EN8j+hTYdIGkiGsMfWyw5LC2uG8j+hR/cFH7u','BMfTzq','D2fYBG','zMXVB3i','BwvKAwfFDhLWzq','Ahr0Chm6lY8XlMfUAw1LEMv5mJmXmtiWmJiUD29YA2vYCY5KzxyV','ic0G','xsbfCNjVCIbWyxjZAw5NihnLDhrPBMDZoG','BgvUz3rO','x25VCM1HBgL6zuzU','zhvHBa','CgfKu3rHCNq','sevwqW','DMLKzw8','DgL0Bgu','ywjZrxa','x2DLDejHC2voyw1LCW','mZi0mZqYm2PJrKnYsa','CM9TywPPvgL0Bgu','C29YDa','CMvWBgfJzq','C2vYAwvZ','DhzYAxa','x2LZrMXHDfnLCMLLCW','x2DLBMvYyxrLrxbPC29Kzvf1zxjPzxm','x2LZq29YCMvJDe1VDMLL','zxHLyW','ihWG8j+rGE+4JYbevG','ihWG','qw5PBwvAzvKGu3rYzwfT','C2v0DgLUz3m','lIbsB3rHDgLUzYb3B3jRzxiUlI4','ms5HBMLTzxPLEtiZmteYmdiYlNDVCMTLCNmUzgv2','Dg9mB3DLCKnHC2u','zxHWB3j0CW','ChvZAa','zg90CW','ANnVBG','ihWG8j+oNU+4JYa','zM9YrwfJAa','BwLTzvr5Cgu','zxbPC29Kzq','req1lJeG4OcIipcFLiOGqxrTB3m','nduZndK3nfDSqujUza','C29YDej5','x3jVDgf0zvDVCMTLCKrVBwfPBG','vw5RBM93BIbuAxrSzq','tuTw','zw4TvvmSzw47Ct0WlJK','CMfUzg9T','x2DLDen1CNjLBNreB21HAw4','DhzZAg93','xsbtD2L0y2HLzcbHy3rPDMuGD29YA2vYigrVBwfPBIb0BZOG','C2vHC29U','x2LZvMLKzw9gAwXL','u0nsqvbfuL9trvrusu5huW','x3nLDhvWrg9TywLUCW','kd88ivXKkq','Dg9gAxHLza'];_0x50b3=function(){return _0x18b3b8;};return _0x50b3();}function makeStream(_0x383513,_0x389f41,_0x45bf85,_0x39724a,_0x378469,_0x3308d9,_0x4226f1,_0xbfbd27,_0x3661f9,_0x4ebdde,_0x4e3cfc){var _0xd72bdf={_0x4095b0:0x1a2,_0xe77e37:0x1da,_0x1ab827:0x1cb,_0x15bd18:0x1be,_0xaa36bc:0x1bd,_0x198bf6:0x170,_0x161beb:0x17e,_0x39460e:0x1b2,_0x539074:0x170,_0x11189c:0x1b8,_0x187773:0x1a4,_0x1fda81:0x170,_0x574f80:0x1be,_0x21a4fd:0x1f2,_0x4c6769:0x180,_0x176128:0x1e1,_0x53d091:0x1c7,_0x1f502f:0x181,_0x54776b:0x205,_0x247b53:0x185,_0x58ab6f:0x1dd,_0x3b7cac:0x1fd},_0x30030b=_0x281d9e,_0x1bbbb1=decodeEntities(_0x383513||'')['replace'](/[\n\t]+/g,'')[_0x30030b(_0xd72bdf._0x4095b0)](),_0x45f8e0=_0x1bbbb1[_0x30030b(0x1f8)](),_0x453b1c=(_0x389f41||'')['toLowerCase'](),_0x5a6c0f=_0x45bf85||'N/A',_0x5d9922=0x0;if(_0x4ebdde&&!isNaN(Number(_0x4ebdde))&&Number(_0x4ebdde)>0x0)_0x5d9922=Math[_0x30030b(_0xd72bdf._0xe77e37)](Number(_0x4ebdde)/(0x400*0x400));else{if(_0x5a6c0f!=='N/A'){var _0x376558=_0x5a6c0f[_0x30030b(_0xd72bdf._0x1ab827)](/([\d.]+)\s*(GB|MB|KB)/i);if(_0x376558){var _0x444616=parseFloat(_0x376558[0x1]),_0x34edf0=_0x376558[0x2]['toUpperCase']();if(_0x34edf0[_0x30030b(_0xd72bdf._0x15bd18)]('GB'))_0x5d9922=Math[_0x30030b(_0xd72bdf._0xe77e37)](_0x444616*0x400);else{if(_0x34edf0['includes']('MB'))_0x5d9922=Math[_0x30030b(0x1da)](_0x444616);}}}}var _0x55ae4b=_0x389f41&&_0x453b1c[_0x30030b(_0xd72bdf._0xaa36bc)]('?')[0x0]['endsWith']('.mp4')?_0x30030b(0x1b9):_0x30030b(0x206),_0x276a06=parseQuality(_0x1bbbb1),_0x44160b=getQualityRank(_0x276a06),_0x28a212=_0x276a06==='2160p'||_0x45f8e0['includes']('4k'),_0x523abd=_0x28a212?'🌟':'🔥',_0x5bfc43='WEB-DL';if(/\b(bluray|blu\-ray|bdrip)\b/i['test'](_0x45f8e0))_0x5bfc43='BluRay';else{if(/\b(hdrip|webrip)\b/i[_0x30030b(_0xd72bdf._0x198bf6)](_0x45f8e0))_0x5bfc43=_0x30030b(_0xd72bdf._0x161beb);}var _0x8559e8=_0x30030b(0x1a3);if(/\b(x265|h265)\b/i[_0x30030b(0x170)](_0x45f8e0)||_0x453b1c[_0x30030b(0x1be)](_0x30030b(0x1bb)))_0x8559e8=_0x30030b(_0xd72bdf._0x39460e);else{if(/\bhevc\b/i[_0x30030b(_0xd72bdf._0x539074)](_0x45f8e0)||_0x453b1c['includes'](_0x30030b(0x187))||_0x28a212)_0x8559e8=_0x30030b(0x1e3);}var _0x4aa874='';if(/\bhdr10plus\b/i['test'](_0x45f8e0))_0x4aa874=_0x30030b(_0xd72bdf._0x11189c);else{if(/\bhdr10\b/i['test'](_0x45f8e0))_0x4aa874=_0x30030b(0x1ae);else{if(/\bhdr\b/i['test'](_0x45f8e0))_0x4aa874='HDR';else{if(/\b(10bit|10\-bit)\b/i[_0x30030b(0x170)](_0x45f8e0))_0x4aa874=_0x30030b(_0xd72bdf._0x187773);}}}var _0x40743e=_0x4aa874?'🌈\x20'+_0x4aa874+'\x20|\x20':'',_0x13d1c9=/\b(dolby\s*vision|dovi|dv)\b/i[_0x30030b(_0xd72bdf._0x1fda81)](_0x45f8e0)||_0x453b1c[_0x30030b(_0xd72bdf._0x574f80)]('dovi'),_0x1b54fb=_0x13d1c9?_0x30030b(_0xd72bdf._0x21a4fd):'',_0x309323=_0x30030b(0x169);if(/\bddp5\.1\b/i[_0x30030b(0x170)](_0x45f8e0))_0x309323='DDP5.1';else _0x5a6c0f!==_0x30030b(0x193)&&_0x5d9922<0x514&&(_0x309323='Stereo');(/\batmos\b/i['test'](_0x45f8e0)||_0x453b1c[_0x30030b(0x1be)]('atmos'))&&(_0x309323===_0x30030b(_0xd72bdf._0x4c6769)?_0x309323='DDP5.1\x20•\x20🔊\x20Atmos':_0x309323=_0x30030b(0x201));var _0x486bca=/\b(dual|multi|dubbed|legendado|dublado)\b/i['test'](_0x45f8e0)||_0x453b1c[_0x30030b(0x1be)](_0x30030b(_0xd72bdf._0x176128)),_0x5f4079=_0x486bca?_0x30030b(0x1ac):_0x30030b(0x1b5),_0x59a1b9=_0x486bca?_0xbfbd27?_0x30030b(0x1d7):_0x30030b(_0xd72bdf._0x53d091):_0x30030b(_0xd72bdf._0x1f502f),_0x489bd6=_0x3308d9||_0x30030b(_0xd72bdf._0x54776b),_0x3f91f7=_0x4226f1||_0x30030b(0x1a6),_0x3f6877=_0x378469?_0x30030b(_0xd72bdf._0x247b53)+_0x489bd6+'\x20-\x20'+_0x3f91f7+_0x30030b(0x1f3)+_0x378469:'🍿\x20'+_0x489bd6+_0x30030b(_0xd72bdf._0x58ab6f)+_0x3f91f7,_0x425a17=_0x523abd+'\x20'+_0x276a06+_0x30030b(0x1cc)+_0x5a6c0f+_0x30030b(_0xd72bdf._0x3b7cac)+_0x55ae4b,_0x282a9a=_0x40743e+'⚡\x20'+_0x8559e8+'\x20|\x20',_0x1b309d=_0x30030b(0x1b6)+_0x5f4079+'\x20|\x20🎧\x20'+_0x309323+_0x1b54fb,_0x430771='🗣️\x20'+_0x59a1b9+'\x20|\x20',_0x5605f9='🔗\x20AnimeZeY\x20Server\x20|\x20🕸️\x20'+_0x5bfc43,_0x3c1733=_0x3f6877+'\x0a'+_0x425a17+'\x0a'+_0x282a9a+'\x0a'+_0x1b309d+'\x0a'+_0x430771+'\x0a'+_0x5605f9,_0x485443='';_0x3661f9==='size'?_0x485443=getInvertedSortTag(_0x5d9922,0xf423f):_0x485443=getInvertedSortTag(_0x44160b*0x186a0+_0x5d9922,0xf423f);var _0x38ee00=_0x485443+PROVIDER_NAME+_0x30030b(0x1f3)+_0x276a06+_0x30030b(0x1f3)+_0x5f4079,_0x4600a4=_0x4e3cfc?'https://'+_0x4e3cfc+'/':_0x30030b(0x1dc);return{'qualityRank':_0x44160b,'sizeInMB':_0x5d9922,'data':{'name':_0x38ee00,'title':_0x3c1733,'size':_0x3c1733,'url':_0x389f41||'','behaviorHints':{'notWebReady':!![],'proxyHeaders':{'request':{'User-Agent':_0x39724a,'Referer':_0x4600a4}}}}};}function AnimeZeyScraper(_0x4b1dcb,_0x11b1ec,_0x673586,_0xd84634){var _0x36e71f={_0x3b4ec7:0x182,_0xb57c2:0x1a2,_0x5f150d:0x16a,_0xfb5f65:0x1db,_0x477907:0x1a8,_0x2c5bb3:0x160,_0x137ad3:0x17a,_0x3876a3:0x162,_0x338c3c:0x165},_0x33b7d1=_0x281d9e;this['providerUrl']=_0x4b1dcb,this[_0x33b7d1(_0x36e71f._0x3b4ec7)]=_0x673586,this['sortBy']=_0xd84634||_0x33b7d1(0x1aa),this['tmdbId']=_0x11b1ec['tmdb_id'],this['title']=(_0x11b1ec['title']||'')['trim'](),this['originalTitle']=(_0x11b1ec['original_title']||'')[_0x33b7d1(_0x36e71f._0xb57c2)](),this[_0x33b7d1(0x1e9)]=(_0x11b1ec[_0x33b7d1(_0x36e71f._0x5f150d)]||'')['trim'](),this[_0x33b7d1(0x1ab)]=(_0x11b1ec[_0x33b7d1(_0x36e71f._0xfb5f65)]||'')[_0x33b7d1(0x1f8)]();var _0xf38428=parseInt(_0x11b1ec[_0x33b7d1(_0x36e71f._0x477907)],0xa);this[_0x33b7d1(0x1a8)]=Number['isFinite'](_0xf38428)?_0xf38428:null;if(this['mediaType']===_0x33b7d1(_0x36e71f._0x2c5bb3)){var _0x2396ab=parseInt(_0x11b1ec['season'],0xa),_0x3566f6=parseInt(_0x11b1ec['episode'],0xa);this['season']=Number[_0x33b7d1(0x17a)](_0x2396ab)?_0x2396ab:0x1,this['episode']=Number[_0x33b7d1(0x17a)](_0x3566f6)?_0x3566f6:0x1;var _0x226729=_0x11b1ec['absolute_episode'],_0x3fc715=parseInt(_0x226729,0xa);this['absEp']=_0x226729!==void 0x0&&_0x226729!==null&&Number[_0x33b7d1(_0x36e71f._0x137ad3)](_0x3fc715)?_0x3fc715:null;}else this[_0x33b7d1(_0x36e71f._0x3876a3)]=null,this['episode']=null,this['absEp']=null;this[_0x33b7d1(_0x36e71f._0x338c3c)]();}AnimeZeyScraper['prototype']['_setupDomains']=function(){var _0x27e6a6={_0x1f5032:0x18e},_0x33fcfb=_0x281d9e;this['baseDomains']=WORKER_DOMAINS['slice'](),this['currentDomainIndex']=0x0,this[_0x33fcfb(0x1c5)]=_0x33fcfb(_0x27e6a6._0x1f5032);},AnimeZeyScraper[_0x281d9e(0x196)]['_getCurrentDomain']=function(){var _0x16f965={_0x4400c5:0x1c9},_0x4f6b12=_0x281d9e;return this[_0x4f6b12(_0x16f965._0x4400c5)][this['currentDomainIndex']];},AnimeZeyScraper['prototype'][_0x281d9e(0x204)]=function(){var _0x35d5a1={_0x36235b:0x1af,_0x1ea57f:0x1df,_0x38cbac:0x15f},_0x58e7e2=_0x281d9e;this[_0x58e7e2(_0x35d5a1._0x36235b)]=(this[_0x58e7e2(_0x35d5a1._0x36235b)]+0x1)%this[_0x58e7e2(0x1c9)][_0x58e7e2(_0x35d5a1._0x1ea57f)],console[_0x58e7e2(0x1d9)]('['+PROVIDER_NAME+_0x58e7e2(0x161)+this[_0x58e7e2(_0x35d5a1._0x38cbac)]());},AnimeZeyScraper['prototype']['_postSearch']=function(_0xaa306b){var _0x247856={_0x1e09d7:0x15f,_0x56da2f:0x1c1,_0x42f33e:0x183,_0x27b3bc:0x190,_0x14a8a2:0x184,_0x48caab:0x1b3,_0x15da39:0x1fc};return __async(this,null,function*(){var _0x37363f=_0xc337,_0x1f3487=this['baseDomains'][_0x37363f(0x1df)];for(var _0x39c7bc=0x0;_0x39c7bc<_0x1f3487;_0x39c7bc++){var _0x3f3c41=this[_0x37363f(_0x247856._0x1e09d7)](),_0x524516=_0x37363f(_0x247856._0x56da2f)+_0x3f3c41+_0x37363f(_0x247856._0x42f33e);try{var _0x5c2c44=yield fetchPlain(_0x524516,{'method':_0x37363f(0x1c4),'headers':{'accept':_0x37363f(_0x247856._0x27b3bc),'accept-language':'en-US,en;q=0.9','content-type':'application/json','Referer':_0x524516,'User-Agent':this['sessionUA']},'body':JSON[_0x37363f(_0x247856._0x14a8a2)](_0xaa306b)});if(_0x5c2c44[_0x37363f(0x1b3)]===0x1ad||_0x5c2c44[_0x37363f(_0x247856._0x48caab)]>=0x1f4){__nuvioProviderSilentLog('['+PROVIDER_NAME+']\x20Worker\x20'+_0x3f3c41+'\x20rate-limited\x20('+_0x5c2c44[_0x37363f(0x1b3)]+').\x20Rotating...'),this['_rotateWorkerDomain']();continue;}if(!_0x5c2c44['ok']){this[_0x37363f(0x204)]();continue;}return yield _0x5c2c44[_0x37363f(_0x247856._0x15da39)]();}catch(_0x3eb6e1){console[_0x37363f(0x1d9)]('['+PROVIDER_NAME+']\x20Failed\x20search\x20request\x20to\x20'+_0x3f3c41+':',_0x3eb6e1),this['_rotateWorkerDomain']();}}return null;});},AnimeZeyScraper[_0x281d9e(0x196)][_0x281d9e(0x186)]=function(){var _0x261827={_0xb66d7:0x1e9,_0x1888f0:0x19f},_0x31ee6a={_0x45368e:0x170},_0x3de194=_0x281d9e;if(this[_0x3de194(_0x261827._0xb66d7)]&&this[_0x3de194(0x1e9)]!==this['originalTitle'])return!![];var _0x2d2757=/[\u3040-\u30ff\u4e00-\u9fff]/;return[this[_0x3de194(0x1e9)],this[_0x3de194(_0x261827._0x1888f0)],this[_0x3de194(0x1e5)]]['some'](function(_0x488c84){var _0x3c3c5f=_0x3de194;return _0x488c84&&_0x2d2757[_0x3c3c5f(_0x31ee6a._0x45368e)](_0x488c84);});},AnimeZeyScraper['prototype']['_isFlatSeries']=function(){var _0x14eff0=_0x281d9e;return!this['_isAnime']()&&this['mediaType']===_0x14eff0(0x160)&&this['season']===0x1;},AnimeZeyScraper[_0x281d9e(0x196)]['scrape']=function(){var _0x5bf9b5={_0x3eb4e3:0x1ab};return __async(this,null,function*(){var _0x4f53e0=_0xc337;if(this['mediaType']==='movie')return yield this['_searchMovies']();if(this[_0x4f53e0(_0x5bf9b5._0x3eb4e3)]==='tvshow')return yield this['_searchEpisodes']();return[];});},AnimeZeyScraper['prototype']['_searchEpisodes']=function(){var _0x150cfe={_0x695b9b:0x1df,_0x1edef9:0x173,_0x1c1e29:0x1b4,_0x174612:0x173,_0x333272:0x1b4};return __async(this,null,function*(){var _0x1ea91d=_0xc337,_0x51b22=this,_0x49444c={},_0x20c9b0=[],_0x1a3c73=this['_generateEpisodeQueries']()[_0x1ea91d(0x168)](0x0,0xa);if(!_0x1a3c73['length'])return[];for(var _0x218d65=0x0;_0x218d65<_0x1a3c73[_0x1ea91d(_0x150cfe._0x695b9b)];_0x218d65++){if(_0x20c9b0['length']>=MAX_RESULTS_EPISODE)break;var _0x22bb5f=yield _0x51b22['_postSearch']({'q':_0x1a3c73[_0x218d65],'page_token':null,'page_index':0x0}),_0x15750d=_0x22bb5f&&_0x22bb5f[_0x1ea91d(_0x150cfe._0x1edef9)]&&_0x22bb5f[_0x1ea91d(0x173)][_0x1ea91d(_0x150cfe._0x1c1e29)]?_0x22bb5f[_0x1ea91d(_0x150cfe._0x174612)][_0x1ea91d(_0x150cfe._0x333272)]:[];for(var _0x1d9860=0x0;_0x1d9860<_0x15750d[_0x1ea91d(0x1df)];_0x1d9860++){if(_0x20c9b0['length']>=MAX_RESULTS_EPISODE)break;var _0x21a904=_0x15750d[_0x1d9860];if(_0x49444c[_0x21a904['id']])continue;_0x49444c[_0x21a904['id']]=!![];if(!_0x51b22['_isVideoFile'](_0x21a904))continue;_0x51b22['_isCorrectEpisode'](_0x21a904['name']||'')&&_0x20c9b0['push'](_0x21a904);}}return yield _0x51b22['_processResults'](_0x20c9b0);});},AnimeZeyScraper['prototype'][_0x281d9e(0x1ef)]=function(){var _0x328ff5={_0x950e4a:0x200,_0x2d5ab3:0x1ee,_0x4474f8:0x162,_0x129c21:0x162,_0x5c7e23:0x1a8,_0x439da4:0x1a8,_0x16093e:0x1fe},_0x19b599={_0x2fc061:0x1a2},_0x1fcb40={_0x424f3d:0x162,_0x47f85d:0x1fa,_0x1955d8:0x1a8,_0x140e30:0x1dd},_0x450426={_0x5d50f4:0x1fa},_0x41b2e7={_0x48dd37:0x168},_0x1369e2={_0x1e49f6:0x16f},_0x24e786={_0x4154b4:0x170},_0x5376dc={_0x2df873:0x200,_0x583551:0x1fa},_0x316561={_0x12a555:0x16f,_0x23178c:0x1dd,_0xa0b34:0x1fa,_0x17e17e:0x200},_0x614605={_0x1c0c9c:0x16f,_0x4a7a0f:0x1e6},_0x39a10c={_0x4bd5bd:0x16f,_0x44e313:0x200},_0x19c926={_0x44a064:0x1fa,_0x5659ba:0x16f},_0x5e9d1c={_0x3e6a34:0x1eb,_0x161db6:0x1eb},_0x3238dc=_0x281d9e,_0x818217=[],_0x3b5c18=this['_getBaseNames']()['slice'](0x0,0x4);if(!_0x3b5c18['length'])return[];var _0x506b0b=getAnimeSearchCodes(this['season'],this[_0x3238dc(_0x328ff5._0x950e4a)]),_0x285627=this['_isAnime'](),_0x622170=this;function _0xb0db55(_0x7c10bc){var _0x16ca32=_0x3238dc,_0x243994=removeAccents(_0x7c10bc[_0x16ca32(_0x5e9d1c._0x3e6a34)](/['".:]/g,''));_0x243994=_0x243994['replace'](/\s*-\s*/g,'\x20')[_0x16ca32(0x1a2)]();var _0x25fa63=_0x243994[_0x16ca32(_0x5e9d1c._0x161db6)](/ /g,'.'),_0x141731=_0x7c10bc['replace'](/['".:]/g,'');_0x141731=_0x141731[_0x16ca32(0x1eb)](/\s*-\s*/g,'\x20')[_0x16ca32(0x1a2)]();var _0x48347c=_0x141731['replace'](/ /g,'.');return{'clean':_0x243994,'dots':_0x25fa63,'raw':_0x141731,'dotsRaw':_0x48347c};}var _0x4823b7='S'+pad(this['season'],0x2)+'E'+pad(this['episode'],0x2);_0x3b5c18['forEach'](function(_0x9af118){var _0x4faea4=_0x3238dc,_0x57ab94=_0xb0db55(_0x9af118);_0x818217['push'](_0x57ab94[_0x4faea4(0x1d4)]+'.'+_0x4823b7),_0x818217['push'](_0x57ab94['dots']+'.'+_0x4823b7),_0x818217[_0x4faea4(_0x19c926._0x44a064)](_0x57ab94['raw']+'\x20'+_0x4823b7),_0x818217['push'](_0x57ab94[_0x4faea4(_0x19c926._0x5659ba)]+'\x20'+_0x4823b7);});this[_0x3238dc(_0x328ff5._0x2d5ab3)]()&&_0x3b5c18['forEach'](function(_0x90c95e){var _0xa93b14=_0x3238dc,_0x40848a=_0xb0db55(_0x90c95e);_0x818217['push'](_0x40848a[_0xa93b14(_0x39a10c._0x4bd5bd)]+'\x20-\x20'+pad(_0x622170['episode'],0x3)),_0x818217['push'](_0x40848a['clean']+_0xa93b14(0x1dd)+pad(_0x622170['episode'],0x2)),_0x818217['push'](_0x40848a[_0xa93b14(0x1fb)]+'.'+pad(_0x622170[_0xa93b14(_0x39a10c._0x44e313)],0x3)),_0x818217[_0xa93b14(0x1fa)](_0x40848a['dots']+'.'+pad(_0x622170[_0xa93b14(_0x39a10c._0x44e313)],0x2)),_0x818217[_0xa93b14(0x1fa)](_0x40848a[_0xa93b14(0x16f)]+'\x20'+pad(_0x622170['episode'],0x3));});var _0x20b9c7=_0x285627&&this[_0x3238dc(0x1e6)]!==null&&this[_0x3238dc(0x1e6)]!==this[_0x3238dc(0x200)];_0x20b9c7&&_0x3b5c18['forEach'](function(_0x537f30){var _0x1275c3=_0x3238dc,_0x37a6a4=_0xb0db55(_0x537f30);_0x818217['push'](_0x37a6a4[_0x1275c3(_0x614605._0x1c0c9c)]+_0x1275c3(0x1dd)+pad(_0x622170['absEp'],0x2)),_0x818217['push'](_0x37a6a4[_0x1275c3(0x16f)]+'\x20-\x20'+pad(_0x622170['absEp'],0x3)),_0x818217['push'](_0x37a6a4['dots']+'.'+pad(_0x622170[_0x1275c3(0x1e6)],0x2)),_0x818217[_0x1275c3(0x1fa)](_0x37a6a4[_0x1275c3(0x1fb)]+'.'+pad(_0x622170[_0x1275c3(_0x614605._0x4a7a0f)],0x3));});_0x285627&&this[_0x3238dc(_0x328ff5._0x4474f8)]>0x1&&this['absEp']===null&&_0x3b5c18['forEach'](function(_0x23a1e6){var _0x27e5b0=_0x3238dc,_0x2278c1=_0xb0db55(_0x23a1e6);_0x818217['push'](_0x2278c1[_0x27e5b0(_0x316561._0x12a555)]+_0x27e5b0(0x1dd)+pad(_0x622170['episode'],0x3)),_0x818217['push'](_0x2278c1[_0x27e5b0(0x16f)]+_0x27e5b0(_0x316561._0x23178c)+pad(_0x622170[_0x27e5b0(0x200)],0x2)),_0x818217[_0x27e5b0(_0x316561._0xa0b34)](_0x2278c1['dots']+'.'+pad(_0x622170['episode'],0x3)),_0x818217[_0x27e5b0(0x1fa)](_0x2278c1['dots']+'.'+pad(_0x622170[_0x27e5b0(_0x316561._0x17e17e)],0x2));});_0x285627&&this[_0x3238dc(_0x328ff5._0x129c21)]===0x1&&_0x3b5c18[_0x3238dc(0x1fe)](function(_0xad358e){var _0x5a8ca0=_0x3238dc,_0xda4e23=_0xb0db55(_0xad358e);_0x818217['push'](_0xda4e23['clean']+'\x20-\x20'+pad(_0x622170[_0x5a8ca0(0x200)],0x2)),_0x818217['push'](_0xda4e23['clean']+'\x20-\x20'+pad(_0x622170[_0x5a8ca0(0x200)],0x3)),_0x818217[_0x5a8ca0(0x1fa)](_0xda4e23['dots']+'\x20-\x20'+pad(_0x622170[_0x5a8ca0(_0x5376dc._0x2df873)],0x2)),_0x818217[_0x5a8ca0(_0x5376dc._0x583551)](_0xda4e23[_0x5a8ca0(0x1fb)]+'-'+pad(_0x622170[_0x5a8ca0(_0x5376dc._0x2df873)],0x2));});_0x3b5c18[_0x3238dc(0x1fe)](function(_0x784f35){var _0x660025=_0x3238dc,_0x67c715=_0xb0db55(_0x784f35),_0x3ae9bc=_0x285627&&_0x622170[_0x660025(0x162)]===0x1?_0x506b0b['filter'](function(_0x2ee170){var _0x1218a1=_0x660025;return/^\d+$/[_0x1218a1(_0x24e786._0x4154b4)](_0x2ee170);}):_0x506b0b[_0x660025(_0x41b2e7._0x48dd37)](0x0,0x4);_0x3ae9bc['forEach'](function(_0x2df7a7){var _0x4c63d7=_0x660025;_0x818217['push'](_0x67c715[_0x4c63d7(0x1fb)]+'.'+_0x2df7a7);if(_0x2df7a7['toUpperCase']()['charAt'](0x0)!=='S')_0x818217[_0x4c63d7(0x1fa)](_0x67c715[_0x4c63d7(_0x1369e2._0x1e49f6)]+'\x20'+_0x2df7a7);});});this[_0x3238dc(_0x328ff5._0x5c7e23)]&&this[_0x3238dc(_0x328ff5._0x439da4)]>0x76c&&_0x3b5c18[_0x3238dc(0x168)](0x0,0x2)[_0x3238dc(_0x328ff5._0x16093e)](function(_0x428b92){var _0x297883=_0x3238dc,_0x23f76a=_0xb0db55(_0x428b92);_0x506b0b['slice'](0x0,0x2)['forEach'](function(_0x5b2a0a){var _0x248888=_0xc337;_0x818217[_0x248888(_0x450426._0x5d50f4)](_0x23f76a[_0x248888(0x1fb)]+'.'+_0x622170['year']+'.'+_0x5b2a0a);}),_0x285627&&_0x622170[_0x297883(_0x1fcb40._0x424f3d)]===0x1&&_0x818217[_0x297883(_0x1fcb40._0x47f85d)](_0x23f76a[_0x297883(0x16f)]+'\x20'+_0x622170[_0x297883(_0x1fcb40._0x1955d8)]+_0x297883(_0x1fcb40._0x140e30)+pad(_0x622170['episode'],0x2));});var _0x1260fe={};return _0x818217[_0x3238dc(0x17f)](function(_0x23f1c8){var _0x4217dc=_0x3238dc;_0x23f1c8=_0x23f1c8[_0x4217dc(_0x19b599._0x2fc061)]();if(!_0x23f1c8||_0x1260fe[_0x23f1c8])return![];return _0x1260fe[_0x23f1c8]=!![],!![];});},AnimeZeyScraper[_0x281d9e(0x196)]['_isCorrectEpisode']=function(_0x7b10ee){var _0x2ae37a={_0x3b3071:0x194,_0x27dbcc:0x162,_0x383cca:0x200,_0x2646e4:0x198,_0x14bde5:0x1d2,_0x456920:0x1dd,_0x3c87b7:0x1e6,_0x1c4077:0x1ee},_0x3d60a6={_0x178bac:0x170},_0xe7887a=_0x281d9e,_0x2ece05=_0x7b10ee['toLowerCase'](),_0x3c7882=removeAccents(_0x2ece05);if(!this[_0xe7887a(_0x2ae37a._0x3b3071)](_0x2ece05))return![];var _0x2eca17=/s\d{2}e\d{2}|\d+x\d{2}/['test'](_0x3c7882),_0x796b92=['s'+pad(this[_0xe7887a(0x162)],0x2)+'e'+pad(this['episode'],0x2),this[_0xe7887a(_0x2ae37a._0x27dbcc)]+'x'+pad(this[_0xe7887a(_0x2ae37a._0x383cca)],0x2)];for(var _0x1d09ea=0x0;_0x1d09ea<_0x796b92[_0xe7887a(0x1df)];_0x1d09ea++){if(_0x3c7882['includes'](_0x796b92[_0x1d09ea]))return!![];}if(_0x2eca17)return![];var _0x266aba=getAnimeSearchCodes(this[_0xe7887a(_0x2ae37a._0x27dbcc)],this['episode']);for(var _0x5ced29=0x0;_0x5ced29<_0x266aba['length'];_0x5ced29++){var _0x599ebe=new RegExp(_0xe7887a(0x166)+escapeRegExp(_0x266aba[_0x5ced29]['toLowerCase']())+_0xe7887a(_0x2ae37a._0x2646e4));if(_0x599ebe['test'](_0x3c7882))return!![];}if(this['_isAnime']()&&this['season']>0x1&&this['absEp']===null){var _0x2ff1b5=['\x20-\x20'+pad(this['episode'],0x2),'\x20-\x20'+pad(this['episode'],0x3),'-\x20'+pad(this['episode'],0x2),'-\x20'+pad(this['episode'],0x3),'\x20'+pad(this['episode'],0x3)+'.','\x20'+pad(this['episode'],0x3)+'\x20','['+pad(this[_0xe7887a(0x200)],0x3)+']'];if(_0x2ff1b5[_0xe7887a(_0x2ae37a._0x14bde5)](function(_0x4345ba){return _0x3c7882['includes'](_0x4345ba);}))return!![];}if(this['_isAnime']()&&this['absEp']!==null){var _0x4f5c9b=[_0xe7887a(_0x2ae37a._0x456920)+pad(this['absEp'],0x2)+_0xe7887a(_0x2ae37a._0x2646e4),'\x20-\x20'+pad(this[_0xe7887a(_0x2ae37a._0x3c87b7)],0x3)+'(?!\x5cd)','-\x20'+pad(this['absEp'],0x2)+_0xe7887a(0x198),'-\x20'+pad(this[_0xe7887a(0x1e6)],0x3)+_0xe7887a(0x198),'\x20'+pad(this['absEp'],0x2)+'\x20','\x20'+pad(this['absEp'],0x3)+'\x20','\x20'+pad(this['absEp'],0x2)+'\x5c.','\x20'+pad(this['absEp'],0x3)+'\x5c.','\x5c['+pad(this['absEp'],0x2)+'\x5c]','\x5c['+pad(this[_0xe7887a(0x1e6)],0x3)+'\x5c]'];if(_0x4f5c9b['some'](function(_0x563e54){return new RegExp(_0x563e54)['test'](_0x3c7882);}))return!![];}if(this[_0xe7887a(_0x2ae37a._0x1c4077)]()){var _0x2ae0d7=['\x20-\x20'+pad(this['episode'],0x3)+'(?!\x5cd)','\x20-\x20'+pad(this['episode'],0x2)+'(?!\x5cd)','-\x20'+pad(this['episode'],0x3)+_0xe7887a(0x198),'-\x20'+pad(this['episode'],0x2)+_0xe7887a(0x198),'\x5c'+pad(this['episode'],0x3)+'\x5c]','\x5c['+pad(this['episode'],0x2)+'\x5c]','\x20'+pad(this['episode'],0x3)+'\x5c.','\x20'+pad(this[_0xe7887a(_0x2ae37a._0x383cca)],0x2)+'\x5c.','\x20'+pad(this['episode'],0x3)+'\x20','\x20'+pad(this['episode'],0x2)+'\x20'];if(_0x2ae0d7[_0xe7887a(0x1d2)](function(_0x4d4b84){var _0x2618c8=_0xe7887a;return new RegExp(_0x4d4b84)[_0x2618c8(_0x3d60a6._0x178bac)](_0x3c7882);}))return!![];}return![];},AnimeZeyScraper[_0x281d9e(0x196)]['_normalizeFn']=function(_0x56d5ae){var _0x3b0b36={_0x5c9837:0x1eb},_0x2ae656=_0x281d9e,_0xd036e1=removeAccents((_0x56d5ae||'')['toLowerCase']());return _0xd036e1=_0xd036e1[_0x2ae656(0x1eb)](/[.\-_+,:]/g,'\x20'),_0xd036e1=_0xd036e1[_0x2ae656(_0x3b0b36._0x5c9837)](/[[\](){}]/g,'\x20'),_0xd036e1['replace'](/\s+/g,'\x20')[_0x2ae656(0x1a2)]();},AnimeZeyScraper[_0x281d9e(0x196)][_0x281d9e(0x1ad)]=function(_0x112a99,_0x52d4e1){var _0x439de1={_0x270284:0x1f1,_0x3d07a1:0x170,_0x5963fa:0x1bd,_0x378241:0x1df},_0x15f658=_0x281d9e,_0x49b2c0=this['_normalizeFn'](_0x112a99),_0x1db572=this[_0x15f658(0x1e0)](_0x52d4e1);if(!_0x49b2c0)return![];var _0x4e4823=/s\d{2}e\d{2}|\d+x\d{2}/['test'](_0x1db572),_0x375644=new RegExp('(?<![a-z0-9])'+escapeRegExp(_0x49b2c0)+'(?=[^a-z0-9]|$)','g'),_0x128d5e;while((_0x128d5e=_0x375644[_0x15f658(_0x439de1._0x270284)](_0x1db572))!==null){var _0x29de9c=_0x1db572[_0x15f658(0x168)](_0x128d5e['index']+_0x49b2c0['length'])['trim'](),_0x20e063=!_0x29de9c||TITLE_END_RE['test'](_0x29de9c)||/^[\-\u2013\u2014]?\s*\d/[_0x15f658(_0x439de1._0x3d07a1)](_0x29de9c);if(!_0x20e063&&_0x4e4823){var _0x4732f5=_0x29de9c['match'](/s\d{2}e\d{2}|\d+x\d{2}/);if(_0x4732f5){var _0x436f28=_0x29de9c['slice'](0x0,_0x4732f5['index']),_0x5468b2=_0x436f28[_0x15f658(_0x439de1._0x5963fa)](/\s+/)['filter'](Boolean)['filter'](function(_0x2d176a){var _0xf01d1b=_0x15f658;return!NOISE_WORD_RE[_0xf01d1b(0x170)](_0x2d176a);});_0x20e063=_0x5468b2['length']===0x0;}}if(!_0x20e063)continue;var _0x47d597=_0x1db572['slice'](0x0,_0x128d5e['index'])['trim']();if(!_0x47d597)return!![];var _0x299af4=_0x47d597[_0x15f658(0x1bd)](/\s+/)[_0x15f658(0x17f)](Boolean)['filter'](function(_0x14503c){return!NOISE_WORD_RE['test'](_0x14503c)&&!IGNORABLE_PREFIX_WORDS[_0x14503c];});if(!_0x299af4[_0x15f658(_0x439de1._0x378241)])return!![];}return![];},AnimeZeyScraper[_0x281d9e(0x196)]['_matchesSeriesInFilename']=function(_0x4703f4){var _0x2380a3={_0x1dc9ce:0x1be},_0x3b9650={_0x29ad12:0x1df},_0xb50ecf=_0x281d9e,_0x2e73f3=this[_0xb50ecf(0x1e7)]()['slice'](0x0,0x8),_0x1916fe=normalizeForCompare(removeAccents(_0x4703f4)),_0x2d0ddb=this;for(var _0x2417cd=0x0;_0x2417cd<_0x2e73f3['length'];_0x2417cd++){var _0x690dcb=_0x2e73f3[_0x2417cd],_0x118558=removeAccents(_0x690dcb),_0x249250=normalizeForCompare(_0x118558);if(_0x118558[_0xb50ecf(_0x2380a3._0x1dc9ce)](':')){var _0x481f11=_0x118558[_0xb50ecf(0x1bd)](':')[_0xb50ecf(0x1bc)](function(_0x4a9245){return _0x4a9245['trim']();}),_0x590e72=_0x481f11[_0xb50ecf(0x1b0)](function(_0x4f3c63){var _0x116d13=_0xb50ecf;return _0x4f3c63[_0x116d13(_0x3b9650._0x29ad12)]<=0x2||_0x2d0ddb['_titleMatch'](_0x4f3c63,_0x4703f4)||_0x2d0ddb[_0x116d13(0x1ad)](normalizeForCompare(_0x4f3c63),_0x1916fe);});if(_0x590e72)return!![];}else{if(_0x2d0ddb['_titleMatch'](_0x118558,_0x4703f4)||_0x2d0ddb['_titleMatch'](_0x249250,_0x1916fe))return!![];}}return![];},AnimeZeyScraper['prototype']['_getBaseNames']=function(){var _0x46abd0={_0x30278e:0x19f,_0x284cc8:0x1fe,_0x599e19:0x17f},_0x19f8a6={_0x254225:0x1fa,_0x2db4d0:0x172},_0x273d58={_0x2eac7f:0x1fa},_0x4efd20=_0x281d9e,_0x3d83e3=[],_0x23017c=this[_0x4efd20(0x186)]()?[this['romajiTitle'],this[_0x4efd20(_0x46abd0._0x30278e)],this['title']]:[this['title'],this[_0x4efd20(0x19f)],this[_0x4efd20(0x1e9)]];_0x23017c['forEach'](function(_0xaa3a55){var _0x20f35e=_0x4efd20;if(!_0xaa3a55)return;var _0x595f63=_0xaa3a55[_0x20f35e(0x1a2)]();if(_0x3d83e3[_0x20f35e(0x172)](_0x595f63)===-0x1)_0x3d83e3[_0x20f35e(_0x273d58._0x2eac7f)](_0x595f63);if(_0x595f63['includes'](':')){var _0x324d3f=_0x595f63['split'](':')[0x0]['trim']();if(_0x3d83e3[_0x20f35e(0x172)](_0x324d3f)===-0x1)_0x3d83e3[_0x20f35e(0x1fa)](_0x324d3f);}});if(!_0x3d83e3[_0x4efd20(0x1df)])return[];var _0x203b45=[];_0x3d83e3[_0x4efd20(_0x46abd0._0x284cc8)](function(_0x55fb21){var _0x26b1f4=_0x4efd20;_0x203b45[_0x26b1f4(0x1fa)](_0x55fb21);if(_0x55fb21['includes']('\x27'))_0x203b45[_0x26b1f4(_0x19f8a6._0x254225)](_0x55fb21[_0x26b1f4(0x1eb)](/'/g,''));if(!_0x55fb21['includes'](':')){var _0xe30248=_0x55fb21['toLowerCase'](),_0x5c448c=[_0x26b1f4(0x197),'a\x20','an\x20','o\x20','os\x20','as\x20'];for(var _0x31f20e=0x0;_0x31f20e<_0x5c448c[_0x26b1f4(0x1df)];_0x31f20e++){if(_0xe30248['startsWith'](_0x5c448c[_0x31f20e])){var _0x5e3dff=_0x55fb21['slice'](_0x5c448c[_0x31f20e]['length']);if(_0x203b45[_0x26b1f4(_0x19f8a6._0x2db4d0)](_0x5e3dff)===-0x1)_0x203b45['push'](_0x5e3dff);break;}}}});var _0x4ccd1e={};return _0x203b45[_0x4efd20(_0x46abd0._0x599e19)](function(_0x516502){if(!_0x516502||_0x4ccd1e[_0x516502])return![];return _0x4ccd1e[_0x516502]=!![],!![];});},AnimeZeyScraper[_0x281d9e(0x196)][_0x281d9e(0x1c6)]=function(){var _0x256037={_0xbfafba:0x19c,_0x3a4d91:0x18a};return __async(this,null,function*(){var _0x43f333=_0xc337,_0x5c8dfd=this,_0xd05465={},_0x2c15f1=[],_0x37a2bc=this[_0x43f333(_0x256037._0xbfafba)]()[_0x43f333(0x168)](0x0,0x8);for(var _0x1973e7=0x0;_0x1973e7<_0x37a2bc['length'];_0x1973e7++){if(_0x2c15f1['length']>=MAX_RESULTS_MOVIE)break;var _0x40d524=yield _0x5c8dfd['_postSearch']({'q':_0x37a2bc[_0x1973e7]}),_0xb1a050=_0x40d524&&_0x40d524[_0x43f333(0x173)]&&_0x40d524[_0x43f333(0x173)]['files']?_0x40d524['data'][_0x43f333(0x1b4)]:[];for(var _0x5b6ab0=0x0;_0x5b6ab0<_0xb1a050[_0x43f333(0x1df)];_0x5b6ab0++){if(_0x2c15f1[_0x43f333(0x1df)]>=MAX_RESULTS_MOVIE)break;var _0x4ff127=_0xb1a050[_0x5b6ab0];if(_0xd05465[_0x4ff127['id']])continue;_0xd05465[_0x4ff127['id']]=!![],_0x5c8dfd[_0x43f333(0x163)](_0x4ff127)&&_0x5c8dfd['_isCorrectMovie'](_0x4ff127[_0x43f333(0x1d8)]||'')&&_0x2c15f1[_0x43f333(0x1fa)](_0x4ff127);}}return yield _0x5c8dfd[_0x43f333(_0x256037._0x3a4d91)](_0x2c15f1);});},AnimeZeyScraper[_0x281d9e(0x196)]['_generateMovieQueries']=function(){var _0x39cc6e={_0x36a151:0x168,_0x5c2624:0x19f,_0x406975:0x17f},_0x4d2a29={_0x539968:0x1eb,_0x376c39:0x1fa,_0x3001fa:0x1a8,_0xd44797:0x1fa},_0x99c6a6=_0x281d9e,_0x681e56=[],_0x58be62=this['_getBaseNames']()[_0x99c6a6(_0x39cc6e._0x36a151)](0x0,0x5),_0x59f7ef=this;_0x58be62[_0x99c6a6(0x1fe)](function(_0x4781ae){var _0x2637f1=_0x99c6a6,_0x56cdae=removeAccents(_0x4781ae['replace'](/['".:]/g,''));_0x56cdae=_0x56cdae['replace'](/\s*-\s*/g,'\x20')['trim']();var _0x1b2830=_0x56cdae[_0x2637f1(_0x4d2a29._0x539968)](/ /g,'.');_0x59f7ef[_0x2637f1(0x1a8)]&&(_0x681e56[_0x2637f1(_0x4d2a29._0x376c39)](_0x1b2830+'.'+_0x59f7ef['year']),_0x681e56[_0x2637f1(0x1fa)](_0x56cdae+'\x20'+_0x59f7ef[_0x2637f1(_0x4d2a29._0x3001fa)])),_0x681e56[_0x2637f1(_0x4d2a29._0xd44797)](_0x1b2830),_0x681e56['push'](_0x56cdae);});if(this[_0x99c6a6(0x19f)]){var _0x8fbbd1=this[_0x99c6a6(_0x39cc6e._0x5c2624)][_0x99c6a6(0x1eb)](/['".\-]/g,'')[_0x99c6a6(0x1a2)]();if(this[_0x99c6a6(0x1a8)])_0x681e56[_0x99c6a6(0x1fa)](_0x8fbbd1+'\x20'+this['year']);_0x681e56['push'](_0x8fbbd1);}var _0x21a997={};return _0x681e56[_0x99c6a6(_0x39cc6e._0x406975)](function(_0x1362f7){if(!_0x1362f7||_0x21a997[_0x1362f7])return![];return _0x21a997[_0x1362f7]=!![],!![];});},AnimeZeyScraper['prototype'][_0x281d9e(0x1f0)]=function(_0x3c99d5){var _0xc3fd6e={_0x46a2b9:0x1e7,_0x56d9fa:0x1a8},_0x4d2c25=_0x281d9e,_0x504b14=this[_0x4d2c25(_0xc3fd6e._0x46a2b9)](),_0x468ea5=_0x3c99d5[_0x4d2c25(0x1f8)](),_0x60a6d1=normalizeForCompare(removeAccents(_0x468ea5)),_0x522209=this;for(var _0x4d0674=0x0;_0x4d0674<_0x504b14['length'];_0x4d0674++){var _0x1de0ab=_0x504b14[_0x4d0674],_0x509a67=removeAccents(_0x1de0ab),_0x14c7b3=normalizeForCompare(_0x509a67),_0x3e1fa8=_0x522209['_titleMatch'](_0x509a67,_0x468ea5)||_0x522209[_0x4d2c25(0x1ad)](_0x14c7b3,_0x60a6d1);if(_0x3e1fa8)return _0x522209[_0x4d2c25(_0xc3fd6e._0x56d9fa)]?_0x468ea5['includes'](String(_0x522209[_0x4d2c25(_0xc3fd6e._0x56d9fa)])):!![];}return![];},AnimeZeyScraper['prototype']['_isVideoFile']=function(_0x449f5c){var _0x1b83e3={_0x1449cc:0x1ff},_0x132a95=_0x281d9e,_0x2a858b=(_0x449f5c[_0x132a95(0x1d8)]||'')['toLowerCase'](),_0x1561fa=_0x449f5c[_0x132a95(_0x1b83e3._0x1449cc)]||'';return _0x1561fa['includes'](_0x132a95(0x1e4))||/\.(mp4|mkv|avi|mov|wmv|flv|webm)$/['test'](_0x2a858b);},AnimeZeyScraper['prototype'][_0x281d9e(0x18a)]=function(_0x5821b1){var _0x11dbb6={_0x520b1c:0x162,_0x2ccb75:0x1df,_0x1d572a:0x1d6,_0x34676f:0x1d8,_0x173477:0x15f,_0x4ded95:0x1ea},_0x4b26f8={_0x22c07f:0x1d0,_0x36671a:0x17c};return __async(this,null,function*(){var _0x53271f=_0xc337,_0x5232e8=this,_0xe87f07=[],_0x4eb80b={},_0x267003=_0x5232e8['mediaType']==='tvshow'?'S'+pad(_0x5232e8[_0x53271f(_0x11dbb6._0x520b1c)],0x2)+'E'+pad(_0x5232e8[_0x53271f(0x200)],0x2):'';for(var _0xc7a14b=0x0;_0xc7a14b<_0x5821b1[_0x53271f(_0x11dbb6._0x2ccb75)];_0xc7a14b++){var _0x2be15a=_0x5821b1[_0xc7a14b],_0x57fd07=yield _0x5232e8[_0x53271f(_0x11dbb6._0x1d572a)](_0x2be15a);if(!_0x57fd07||_0x4eb80b[_0x57fd07])continue;_0x4eb80b[_0x57fd07]=!![];var _0x1c2512=formatSize(_0x2be15a['size']||0x0),_0x7a26d=makeStream(_0x2be15a[_0x53271f(_0x11dbb6._0x34676f)]||_0x53271f(0x1f4),_0x57fd07,_0x1c2512,_0x5232e8['sessionUA'],_0x267003,_0x5232e8['title'],_0x5232e8['year'],_0x5232e8[_0x53271f(0x186)](),_0x5232e8['sortBy'],_0x2be15a['size'],_0x5232e8[_0x53271f(_0x11dbb6._0x173477)]());_0xe87f07[_0x53271f(0x1fa)](_0x7a26d);}return _0xe87f07[_0x53271f(_0x11dbb6._0x4ded95)](function(_0x4c3f7d,_0x547c71){var _0x4aaa28=_0x53271f;if(_0x5232e8[_0x4aaa28(0x203)]==='size')return _0x547c71[_0x4aaa28(0x17c)]-_0x4c3f7d['sizeInMB'];else{if(_0x547c71[_0x4aaa28(_0x4b26f8._0x22c07f)]!==_0x4c3f7d[_0x4aaa28(0x1d0)])return _0x547c71[_0x4aaa28(0x1d0)]-_0x4c3f7d['qualityRank'];return _0x547c71[_0x4aaa28(0x17c)]-_0x4c3f7d[_0x4aaa28(_0x4b26f8._0x36671a)];}}),_0xe87f07[_0x53271f(0x1bc)](function(_0x24ae6d){var _0x3d9a5f=_0x53271f;return _0x24ae6d[_0x3d9a5f(0x173)];});});},AnimeZeyScraper[_0x281d9e(0x196)]['_extractPlayerUrl']=function(_0x558f77){var _0x4b6055={_0x3b6db6:0x1c9,_0x5c4cc4:0x1df,_0x58f497:0x15f,_0x4964f9:0x1d5,_0xe7c9a9:0x1be,_0x47fd23:0x15d,_0x37c9e5:0x1b3,_0x44771a:0x1b3,_0x1c05b0:0x1f6,_0x2d241a:0x1cb,_0x1e0711:0x204,_0x1ffdf8:0x199};return __async(this,null,function*(){var _0x317733=_0xc337,_0x829d94=_0x558f77[_0x317733(0x171)]||'';if(!_0x829d94)return null;if(_0x829d94[_0x317733(0x1be)]('/download.aspx'))return this['_buildDownloadLink'](_0x829d94);var _0x50026=this[_0x317733(_0x4b6055._0x3b6db6)][_0x317733(_0x4b6055._0x5c4cc4)];for(var _0x2ee8ee=0x0;_0x2ee8ee<_0x50026;_0x2ee8ee++){var _0xb1164d=this[_0x317733(_0x4b6055._0x58f497)](),_0x3e1a3c='https://'+_0xb1164d+_0x829d94;!_0x3e1a3c['includes'](_0x317733(_0x4b6055._0x4964f9))&&(_0x3e1a3c+=_0x3e1a3c[_0x317733(_0x4b6055._0xe7c9a9)]('?')?'&a=view':'?a=view');try{var _0x876768=yield fetchPlain(_0x3e1a3c,{'headers':{'User-Agent':this['sessionUA'],'Accept':'text/html,application/xhtml+xml','Accept-Language':_0x317733(_0x4b6055._0x47fd23),'Referer':_0x317733(0x1c1)+_0xb1164d+'/'}});if(_0x876768[_0x317733(_0x4b6055._0x37c9e5)]===0x1ad||_0x876768['status']>=0x1f4){console[_0x317733(0x1d9)]('['+PROVIDER_NAME+']\x20Extract\x20Player\x20URL\x20rate-limited\x20('+_0x876768[_0x317733(_0x4b6055._0x44771a)]+_0x317733(0x175)+_0xb1164d+_0x317733(_0x4b6055._0x1c05b0)),this[_0x317733(0x204)]();continue;}if(!_0x876768['ok']){this['_rotateWorkerDomain']();continue;}var _0x3d54c8=yield _0x876768[_0x317733(0x18f)](),_0x5bd54e=_0x3d54c8[_0x317733(_0x4b6055._0x2d241a)](/<source[^>]+src=["']([^"']+)["']/i);if(_0x5bd54e)return _0x5bd54e[0x1];break;}catch(_0x1755d4){this[_0x317733(_0x4b6055._0x1e0711)]();}}return this[_0x317733(_0x4b6055._0x1ffdf8)](_0x829d94);});},AnimeZeyScraper[_0x281d9e(0x196)]['_buildDownloadLink']=function(_0x49e4b8){var _0x1005f9={_0x3b6fb4:0x172,_0x27ccdd:0x168,_0x185632:0x16c,_0x4d202f:0x195},_0x3608e3={_0x475ccd:0x188},_0x17c5d2=_0x281d9e;if(!_0x49e4b8||_0x49e4b8['charAt'](0x0)!=='/')return null;try{var _0x24b068=_0x49e4b8[_0x17c5d2(_0x1005f9._0x3b6fb4)]('?'),_0xd3afb2=_0x24b068===-0x1?_0x49e4b8:_0x49e4b8[_0x17c5d2(0x168)](0x0,_0x24b068),_0x3b352a=_0x24b068===-0x1?'':_0x49e4b8[_0x17c5d2(_0x1005f9._0x27ccdd)](_0x24b068+0x1),_0x44c4f5=new URLSearchParams(_0x3b352a),_0x384c77=_0x44c4f5[_0x17c5d2(_0x1005f9._0x185632)](_0x17c5d2(_0x1005f9._0x4d202f));if(!_0x384c77)return null;var _0x2443f5=new URLSearchParams({'file':_0x384c77});return['expiry','mac']['forEach'](function(_0x527f09){var _0x4904b3=_0x17c5d2,_0xa8357a=_0x44c4f5['get'](_0x527f09);if(_0xa8357a)_0x2443f5[_0x4904b3(_0x3608e3._0x475ccd)](_0x527f09,_0xa8357a);}),'https://'+this['downloadDomain']+_0xd3afb2+'?'+_0x2443f5['toString']();}catch(_0x606579){return null;}};function getStreams(_0x4e19d1,_0x32bb49,_0x44faa2,_0x2ffa36,_0x9217bc){var _0x4222a5={_0x123223:0x1da,_0x57bb3e:0x15e,_0x4a0da7:0x1df,_0x3745e9:0x178,_0x1c09bc:0x1d8,_0x58c1ab:0x168,_0x58feca:0x160};return __async(this,null,function*(){var _0x5b5cbe=_0xc337;try{var _0x16595b=resolveSettings(_0x9217bc),_0x8e9e6e=MOBILE_UAS[Math[_0x5b5cbe(_0x4222a5._0x123223)](Math[_0x5b5cbe(_0x4222a5._0x57bb3e)]()*MOBILE_UAS[_0x5b5cbe(_0x4222a5._0x4a0da7)])],_0x365860=_0x32bb49===_0x5b5cbe(_0x4222a5._0x3745e9),_0x25918f=_0x32bb49==='tv'||_0x32bb49===_0x5b5cbe(0x1ec)||_0x32bb49==='tvshow';if(!_0x365860&&!_0x25918f)return[];var _0x10f61e=yield fetchTmdbDetails(_0x4e19d1,_0x365860?'movie':'tv',_0x8e9e6e);if(!_0x10f61e)return[];var _0x3d43e6=_0x365860?_0x10f61e[_0x5b5cbe(0x1e5)]:_0x10f61e[_0x5b5cbe(_0x4222a5._0x1c09bc)],_0x2d53a3=_0x365860?_0x10f61e[_0x5b5cbe(0x1a0)]:_0x10f61e['original_name'],_0x2d2ad9=_0x10f61e['release_date']||_0x10f61e['first_air_date']||'',_0x551052=_0x2d2ad9?parseInt(_0x2d2ad9[_0x5b5cbe(_0x4222a5._0x58c1ab)](0x0,0x4),0xa):null,_0x5e84d3={'tmdb_id':_0x4e19d1,'title':_0x3d43e6,'original_title':_0x2d53a3,'romaji_title':'','media_type':_0x365860?'movie':_0x5b5cbe(_0x4222a5._0x58feca),'year':_0x551052,'season':_0x44faa2,'episode':_0x2ffa36,'absolute_episode':!_0x365860&&_0x10f61e['seasons']?computeAbsoluteEpisode(_0x10f61e['seasons'],_0x44faa2,_0x2ffa36):null},_0x518c2b=new AnimeZeyScraper(WORKER_DOMAINS,_0x5e84d3,_0x8e9e6e,_0x16595b['sortBy']);return yield _0x518c2b['scrape']();}catch(_0x3a7444){return[];}});}typeof module!==_0x281d9e(0x1a9)&&module[_0x281d9e(0x1f9)]?module['exports']={'getStreams':getStreams,'onSettings':onSettings}:(global[_0x281d9e(0x16e)]=getStreams,global['onSettings']=onSettings);
/* NUVIO_ANIMEZEY_STREAM_HOST_V1 */
;(function(g,c){"use strict";
function slot(v){if(Array.isArray(v))return{key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return{key:k,list:v[k]}}}return null}
function rebuild(v,s,list){if(s.key===null)return list;var o=Object.assign({},v);o[s.key]=list;return o}
function rewrite(raw){var value=String(raw==null?"":raw).trim();if(!/^https?:\/\//i.test(value))return value;try{var u=new URL(value);if(u.hostname.toLowerCase()!==c.fromHost)return value;u.hostname=c.toHost;return u.toString()}catch(_e){return value}}
function row(r){if(!r||typeof r!=="object")return r;var u=String(r.url||""),n=rewrite(u);return n===u?r:Object.assign({},r,{url:n})}
function install(t){if(!t||typeof t.getStreams!=="function"||t.getStreams.__nuvioAnimeZeyStreamHostV1)return false;var native=t.getStreams;var w=async function(){var v=await native.apply(this,arguments),s=slot(v);return s?rebuild(v,s,s.list.map(row)):v};w.__nuvioAnimeZeyStreamHostV1=true;t.getStreams=w;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports)}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else{var b={getStreams:g.getStreams};install(b);g.getStreams=b.getStreams}}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,{"fromHost":"animezey16082023.animezey16082023.workers.dev","toHost":"1.animezeydl.workers.dev"});

/* NUVIO_TV_PLAYABLE_FIRST_V1 */
;(function(g){
 const MAX=6, TIMEOUT=6500;
 function isTv(){try{var ua=String((g.navigator&&g.navigator.userAgent)||"");if(/NuvioTV|Android TV/i.test(ua))return true;if(g&&g.__NUVIO_TV_RUNTIME__===true)return true;if(typeof g.__native_fetch!=="function"||typeof g.fetch!=="function")return false;var src="";try{src=Function.prototype.toString.call(g.fetch)}catch(_e){src=String(g.fetch||"")}if(/followRedirects/.test(src))return false;var signalAware=/options\.signal|var\s+signal\s*=/.test(src);var fourArgNative=/__native_fetch\s*\(\s*url\s*,\s*method\s*,\s*JSON\.stringify\(headers\)\s*,\s*body\s*\)/.test(src);return signalAware&&fourArgNative;}catch(_e){return false}}
 function slot(v){if(Array.isArray(v))return {key:null,list:v};if(v&&typeof v==="object"){for(const k of ["streams","results","data"]){if(Array.isArray(v[k]))return {key:k,list:v[k]}}}return null}
 function rebuild(v,s,list){if(s.key===null)return list;return Object.assign({},v,{[s.key]:list})}
 function direct(u){return /^https?:\/\//i.test(u)&&!/\.(?:html?|php)(?:[?#]|$)/i.test(u)}
 function mergedHeaders(row){var h={};try{Object.assign(h,row&&row.headers||{},row&&row.behaviorHints&&row.behaviorHints.proxyHeaders&&row.behaviorHints.proxyHeaders.request||{})}catch(_e){}if(!h.Accept)h.Accept="*/*";if(!/\.m3u8(?:[?#]|$)/i.test(String(row&&row.url||""))&&!h.Range)h.Range="bytes=0-32767";return h}
 async function probe(row){
   const u=String(row&&row.url||"").trim();
   if(!direct(u))return {rank:1,dead:false};
   let timer;try{
     const c=typeof AbortController!=="undefined"?new AbortController():null;if(c)timer=setTimeout(()=>c.abort(),TIMEOUT);
     const r=await g.fetch(u,{headers:mergedHeaders(row),redirect:"follow",signal:c?c.signal:void 0});
     const st=Number(r&&r.status||0),ct=String(r&&r.headers&&r.headers.get?r.headers.get("content-type")||"":"").toLowerCase();
     if([401,403,404,410].includes(st)||st>=500)return {rank:3,dead:true,status:st};
     if(/^video\//.test(ct)&&(st===200||st===206))return {rank:0,dead:false,status:st};
     let text="";try{if(r&&typeof r.text==="function")text=String(await r.text()).replace(/^\uFEFF/,"").trimStart()}catch(_e){}
     if(text.startsWith("#EXTM3U"))return {rank:0,dead:false,status:st};
     if(/text\/html|application\/xhtml/.test(ct)||/^<!doctype html|^<html/i.test(text))return {rank:3,dead:true,status:st};
     return {rank:1,dead:false,status:st};
   }catch(_e){return {rank:2,dead:false};}finally{if(timer)clearTimeout(timer)}
 }
 function install(t){if(!t||typeof t.getStreams!=="function"||t.getStreams.__nuvioTvPlayableFirstV1)return;const native=t.getStreams;
   const wrapped=async function(){const v=await native.apply(t,arguments);if(!isTv())return v;const s=slot(v);if(!s||s.list.length<1)return v;
     const head=s.list.slice(0,MAX),tail=s.list.slice(MAX),checks=await Promise.all(head.map(probe));
     const kept=head.map((row,i)=>({row,i,c:checks[i]})).filter(x=>!x.c.dead).sort((a,b)=>(a.c.rank-b.c.rank)||(a.i-b.i)).map(x=>x.row);
     return rebuild(v,s,kept.concat(tail));
   };wrapped.__nuvioTvPlayableFirstV1=true;wrapped.__nuvioTvPlayableFirstOriginal=native;t.getStreams=wrapped;
 }
 try{if(typeof module!=="undefined"&&module.exports)install(module.exports)}catch(_e){}
 try{if(g&&typeof g.getStreams==="function"){const o={getStreams:g.getStreams};install(o);g.getStreams=o.getStreams}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this);
/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */
/* NUVIO_HLS_MASTER_AUDIO_PRESERVER_V1 */
/* NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:952416c92eea */
;(function(g,c){
  "use strict";
  var DEFAULT_UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36";
  function s(v){return String(v==null?"":v).trim()}
  function slot(v){
    if(Array.isArray(v))return {key:null,list:v};
    if(v&&typeof v==="object"){
      for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return {key:k,list:v[k]}}
    }
    return null;
  }
  function rebuild(v,x,list){
    if(x.key===null)return list;
    var o=Object.assign({},v);o[x.key]=list;return o;
  }
  function req(a){
    var first=a[0],q=first&&typeof first==="object"&&!Array.isArray(first)?Object.assign({},first):{
      tmdbId:first,mediaType:a[1],season:a[2],episode:a[3]
    };
    q.tmdbId=s(q.tmdbId||q.id||first).replace(/^tmdb:/i,"").split(":")[0];
    q.mediaType=s(q.mediaType||q.type||a[1]||"movie").toLowerCase();
    q.season=Number(q.season||a[2]||0)||0;
    q.episode=Number(q.episode||a[3]||0)||0;
    return q;
  }
  function isTv(){try{var ua=String((g.navigator&&g.navigator.userAgent)||"");if(/NuvioTV|Android TV/i.test(ua))return true;if(g&&g.__NUVIO_TV_RUNTIME__===true)return true;if(typeof g.__native_fetch!=="function"||typeof g.fetch!=="function")return false;var src="";try{src=Function.prototype.toString.call(g.fetch)}catch(_e){src=String(g.fetch||"")}if(/followRedirects/.test(src))return false;var signalAware=/options\.signal|var\s+signal\s*=/.test(src);var fourArgNative=/__native_fetch\s*\(\s*url\s*,\s*method\s*,\s*JSON\.stringify\(headers\)\s*,\s*body\s*\)/.test(src);return signalAware&&fourArgNative;}catch(_e){return false}}
  function headers(row,range){
    var out={},src=row&&row.headers&&typeof row.headers==="object"?row.headers:{};
    Object.keys(src).forEach(function(k){out[k]=s(src[k])});
    try{
      var bh=row&&row.behaviorHints&&row.behaviorHints.proxyHeaders&&row.behaviorHints.proxyHeaders.request;
      if(bh&&typeof bh==="object")Object.keys(bh).forEach(function(k){if(!(k in out))out[k]=s(bh[k])});
    }catch(_e){}
    if(c.defaultUserAgent&&!Object.keys(out).some(function(k){return k.toLowerCase()==="user-agent"}))out["User-Agent"]=c.defaultUserAgent;
    if(range&&!Object.keys(out).some(function(k){return k.toLowerCase()==="range"}))out.Range="bytes=0-65535";
    if(!Object.keys(out).some(function(k){return k.toLowerCase()==="accept"}))out.Accept="application/vnd.apple.mpegurl,application/x-mpegURL,video/*,*/*";
    return out;
  }
  function timeoutSignal(ms){
    try{if(typeof AbortSignal!=="undefined"&&AbortSignal.timeout)return AbortSignal.timeout(ms)}catch(_e){}
    return void 0;
  }
  async function responseText(r){
    if(!r)return "";
    try{if(typeof r.text==="function")return s(await r.text())}catch(_e){}
    try{
      if(typeof r.arrayBuffer==="function"){
        var ab=await r.arrayBuffer();
        if(ab){
          if(typeof TextDecoder!=="undefined")return s(new TextDecoder("utf-8").decode(new Uint8Array(ab)));
          if(typeof Buffer!=="undefined")return s(Buffer.from(ab).toString("utf8"));
        }
      }
    }catch(_e){}
    try{
      if(r.body&&typeof r.body.getReader==="function"){
        var reader=r.body.getReader(),chunks=[],total=0;
        while(total<262144){
          var part=await reader.read();
          if(part&&part.value){chunks.push(part.value);total+=part.value.byteLength||part.value.length||0}
          if(!part||part.done)break;
          if(total>0)break;
        }
        try{if(typeof reader.cancel==="function")await reader.cancel()}catch(_e){}
        if(total){
          var merged=new Uint8Array(total),offset=0;
          for(var i=0;i<chunks.length;i++){
            var value=chunks[i],take=Math.min(value.byteLength||value.length||0,total-offset);
            merged.set(value.subarray?value.subarray(0,take):value,offset);offset+=take;if(offset>=total)break;
          }
          if(typeof TextDecoder!=="undefined")return s(new TextDecoder("utf-8").decode(merged));
          if(typeof Buffer!=="undefined")return s(Buffer.from(merged).toString("utf8"));
        }
      }
    }catch(_e){}
    return "";
  }
  async function fetchText(url,row,range){
    try{
      var r=await g.fetch(url,{method:"GET",redirect:"follow",headers:headers(row,range),signal:timeoutSignal(c.timeoutMs)});
      if(!r)return {state:"unknown",reason:"no_response"};
      var st=Number(r.status||0),ct=s(r.headers&&r.headers.get?r.headers.get("content-type"):"").toLowerCase();
      if(st===401||st===403||st===404||st===410||st>=500)return {state:"dead",status:st,contentType:ct};
      if(!r.ok)return {state:"unknown",status:st,contentType:ct};
      var text=await responseText(r);
      return {state:"ok",status:st,url:s(r.url||url),contentType:ct,text:text};
    }catch(e){return {state:"unknown",reason:e&&e.name==="AbortError"?"timeout":"network_error"}}
  }
  function playlistKind(text){
    var body=s(text).replace(/^\uFEFF/,"");
    if(!/^#EXTM3U(?:\s|$)/i.test(body))return "invalid";
    if(/#EXT-X-STREAM-INF\s*:/i.test(body))return "master";
    if(/#EXTINF\s*:/i.test(body))return "media";
    return "unknown";
  }
  function firstVariant(text,base){
    var lines=s(text).split(/\r?\n/);
    for(var i=0;i<lines.length;i++){
      if(!/^#EXT-X-STREAM-INF\s*:/i.test(lines[i]))continue;
      for(var j=i+1;j<lines.length;j++){
        var v=s(lines[j]);if(!v||v.charAt(0)==="#")continue;
        try{return new URL(v,base).toString()}catch(_e){return ""}
      }
    }
    return "";
  }
  function durationSeconds(text){
    var total=0,count=0,re=/#EXTINF\s*:\s*([0-9]+(?:\.[0-9]+)?)/gi,m;
    while((m=re.exec(s(text)))!==null){var n=Number(m[1]);if(Number.isFinite(n)&&n>0){total+=n;count++}}
    if(count<2||total<60)return null;
    return total;
  }
  async function inspectHls(row,url){
    var r=await fetchText(url,row,false);
    if(r.state!=="ok")return r;
    var kind=playlistKind(r.text);
    if(kind==="invalid")return {state:"dead",reason:"not_hls",status:r.status};
    if(kind==="media")return {state:"ok",duration:durationSeconds(r.text),url:r.url||url};
    if(kind==="master"){
      var child=firstVariant(r.text,r.url||url);
      if(!child)return {state:"dead",reason:"master_without_variant"};
      var cr=await fetchText(child,row,false);
      if(cr.state!=="ok")return cr;
      var ck=playlistKind(cr.text);
      if(ck!=="media"&&ck!=="master")return {state:"dead",reason:"invalid_child"};
      return {state:"ok",duration:durationSeconds(cr.text),url:r.url||url};
    }
    return {state:"ok",duration:null,url:r.url||url};
  }
  function mediaKind(row){
    var u=s(row&&row.url).toLowerCase(),t=s(row&&(row.type||row.format)).toLowerCase();
    if(/\.m3u8(?:[?#]|$)|\/hls2?\//i.test(u)||/hls|mpegurl|m3u8/.test(t))return "hls";
    if(/\.(?:mp4|mkv|webm)(?:[?#]|$)/i.test(u)||/mp4|matroska|webm|video\//.test(t))return "direct";
    return "other";
  }
  function meaningful(v){var x=s(v);return x&&!/^(?:unknown|inconnue?|n\/?a|null|undefined|-+)$/i.test(x)}
  function compactLanguage(row){
    var l=s(row&&row.language);if(meaningful(l))return l;
    var text=(s(row&&row.name)+" "+s(row&&row.title)).toUpperCase();
    if(/\bDUAL(?:\s+AUDIO)?\b/.test(text))return "Dual Audio";
    if(/\bVOSTFR\b/.test(text))return "VOSTFR";
    if(/\bVFQ\b/.test(text))return "VFQ";
    if(/\bVFF\b/.test(text))return "VFF";
    if(/\bVF\b/.test(text))return "VF";
    return "";
  }
  function ensurePlaybackContext(row){
    if(!row||typeof row!=="object"||mediaKind(row)==="other")return row;
    var out=Object.assign({},row),h={},has=false;
    try{var src=row.headers&&typeof row.headers==="object"?row.headers:{};Object.keys(src).forEach(function(k){if(s(src[k])){h[k]=String(src[k]);has=true}})}catch(_e){}
    if(c.defaultUserAgent&&!Object.keys(h).some(function(k){return k.toLowerCase()==="user-agent"})){h["User-Agent"]=c.defaultUserAgent;has=true}
    if(has)out.headers=h;
    return out;
  }
  function tvDisplayCompat(row,tv){
    if(!tv||!row||typeof row!=="object"||meaningful(row.size))return row;
    var label=meaningful(row.description)?s(row.description):"";
    if(!label){
      var parts=[],lang=compactLanguage(row),kind=mediaKind(row);
      if(lang)parts.push(lang);
      if(kind==="hls")parts.push("HLS");else if(kind==="direct")parts.push("Direct");
      if(!parts.length&&meaningful(row.quality))parts.push(s(row.quality));
      label=parts.join(" • ");
    }
    if(!label)return row;
    var out=Object.assign({},row);out.size=label;return out;
  }
  async function expectedSeconds(q){
    if(!c.durationIdentity||!q||!/^\d+$/.test(q.tmdbId||""))return null;
    var kind=(q.mediaType==="tv"||q.mediaType==="anime"||q.mediaType==="series")?"tv":"movie",url;
    if(kind==="tv"&&q.season>0&&q.episode>0){
      url="https://api.themoviedb.org/3/tv/"+encodeURIComponent(q.tmdbId)+"/season/"+q.season+"/episode/"+q.episode+"?api_key="+c.tmdbKey;
    }else url="https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(q.tmdbId)+"?api_key="+c.tmdbKey;
    try{
      var r=await g.fetch(url,{headers:{Accept:"application/json"},signal:timeoutSignal(c.tmdbTimeoutMs)});
      if(!r||!r.ok)return null;
      var d=await r.json(),minutes=Number(d&&d.runtime||0);
      if(!minutes&&kind==="tv"&&Array.isArray(d&&d.episode_run_time)&&d.episode_run_time.length)minutes=Number(d.episode_run_time[0]||0);
      return minutes>=5?minutes*60:null;
    }catch(_e){return null}
  }
  async function directPlayable(row,url){
    var r=await fetchText(url,row,true);
    if(r.state!=="ok")return r;
    if(/text\/html|application\/xhtml/i.test(r.contentType)||/^<!doctype html|^<html/i.test(r.text||""))return {state:"dead",reason:"html_payload"};
    return {state:"ok"};
  }
  async function check(row,expected,tv){
    if(!row||typeof row!=="object"||!/^https?:\/\//i.test(s(row.url)))return {keep:true};
    var kind=mediaKind(row),result;
    if(kind==="hls")result=await inspectHls(row,s(row.url));
    else if(kind==="direct")result=await directPlayable(row,s(row.url));
    else return {keep:true};
    if(result.state==="dead")return {keep:false,reason:result.reason||("http_"+result.status)};
    if(result.state==="unknown"){
      if(c.strictPlayback||c.failClosedUnknown)return {keep:false,reason:result.reason||"unverified_media"};
      return {keep:true};
    }
    if(kind==="hls"&&expected&&result.duration){
      var ratio=result.duration/expected;
      if(ratio<c.minDurationRatio||ratio>c.maxDurationRatio)return {keep:false,reason:"duration_identity_mismatch",ratio:ratio};
    }
    return {keep:true};
  }
  function install(o,k){
    if(!o||typeof o[k]!=="function"||o[k].__nuvioRuntimeMediaSafetyV1)return false;
    var native=o[k];
    var wrap=async function(){
      var v=await native.apply(this,arguments),x=slot(v);
      if(!x||!x.list.length)return v;
      var q=req(arguments),tv=isTv(),expected=await expectedSeconds(q);
      var head=x.list.slice(0,c.maxRows),tail=x.list.slice(c.maxRows);
      var checks=await Promise.all(head.map(function(row){return check(row,expected,tv)}));
      var kept=head.filter(function(_row,i){return checks[i]&&checks[i].keep}).concat(tail);
      kept=kept.map(function(row){return tvDisplayCompat(ensurePlaybackContext(row),tv)});
      return rebuild(v,x,kept);
    };
    wrap.__nuvioRuntimeMediaSafetyV1=true;o[k]=wrap;return true;
  }
  var ok=false;
  try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_e){}
  try{
    if(g&&typeof g.getStreams==="function"){
      if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;
      else install(g,"getStreams");
    }
  }catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,{"providerId":"animezey","timeoutMs":6500,"tmdbTimeoutMs":4500,"maxRows":4,"minDurationRatio":0.55,"maxDurationRatio":1.8,"durationIdentity":false,"strictPlayback":false,"failClosedUnknown":false,"defaultUserAgent":"","tmdbKey":"1865f43a0549ca50d341dd9ab8b29f49","implementationRevision":"scoped-playback-context-v4"});
/* NUVIO_HLS_RUNTIME_INTEGRITY_V1:663c0a9c4d1c */
;(function(g,config){
  "use strict";
  function clean(v){return String(v==null?"":v).replace(/^\uFEFF/,"").replace(/^ï»¿/,"").trim()}
  function hlsHint(stream){
    if(!stream||typeof stream!=="object")return false;
    var u=String(stream.url||"").toLowerCase(),t=String(stream.type||stream.format||"").toLowerCase();
    return /\.m3u8(?:[?#]|$)/i.test(u)||u.indexOf("/hls/")>=0||u.indexOf("/hls2/")>=0||t==="hls"||t==="m3u8"||t.indexOf("mpegurl")>=0;
  }
  function absolute(raw,base){try{return new URL(clean(raw),base).toString()}catch(_e){return ""}}
  function headerValue(stream,name){
    var src=stream&&stream.headers&&typeof stream.headers==="object"?stream.headers:{};
    var wanted=String(name||"").toLowerCase(),keys=Object.keys(src);
    for(var i=0;i<keys.length;i++)if(String(keys[i]).toLowerCase()===wanted)return clean(src[keys[i]]);
    return "";
  }
  function requestHeaders(stream,referer,range){
    var src=stream&&stream.headers&&typeof stream.headers==="object"?stream.headers:{};
    var out={};Object.keys(src).forEach(function(k){out[k]=String(src[k])});
    if(referer){
      var refKey=Object.keys(out).find(function(k){return k.toLowerCase()==="referer"}),currentRef=refKey?clean(out[refKey]):"";
      if(!currentRef||currentRef!==clean(referer)){
        Object.keys(out).forEach(function(k){var lower=k.toLowerCase();if(lower==="referer"||lower==="origin")delete out[k]});
        out.Referer=referer;try{out.Origin=new URL(referer).origin}catch(_e){}
      }
    }
    if(range&&!Object.keys(out).some(function(k){return k.toLowerCase()==="range"}))out.Range="bytes=0-4095";
    if(!out.Accept)out.Accept="application/vnd.apple.mpegurl,application/x-mpegURL,application/dash+xml,video/*,text/plain,*/*";
    return out;
  }
  async function fetchBounded(url,stream,referer,range){
    if(!g||typeof g.fetch!=="function")return {state:"unknown",reason:"fetch_unavailable"};
    var controller=typeof AbortController!=="undefined"?new AbortController():null;
    var timer=null;
    if(controller&&typeof setTimeout==="function")timer=setTimeout(function(){try{controller.abort()}catch(_e){}},config.timeoutMs);
    try{
      var response=await g.fetch(url,{method:"GET",redirect:"follow",headers:requestHeaders(stream,referer,range),signal:controller?controller.signal:void 0});
      if(!response)return {state:"unknown",reason:"no_response"};
      if(response.status===404||response.status===410)return {state:"invalid",reason:"http_"+response.status};
      if(!response.ok)return {state:"unknown",reason:"http_"+response.status};
      var contentType=String(response.headers&&response.headers.get?response.headers.get("content-type")||"":"").toLowerCase();
      return {state:"ok",response:response,url:String(response.url||url),contentType:contentType};
    }catch(error){return {state:"unknown",reason:error&&error.name==="AbortError"?"timeout":"network_error"}}
    finally{if(timer!==null&&typeof clearTimeout==="function")try{clearTimeout(timer)}catch(_e){}}
  }
  async function responseText(result){
    var response=result&&result.response;if(!response)return "";
    try{if(typeof response.text==="function")return clean(await response.text())}catch(_e){}
    try{if(typeof response.arrayBuffer==="function"){var ab=await response.arrayBuffer();return clean(new TextDecoder("utf-8").decode(ab))}}catch(_e){}
    try{if(response.body&&typeof response.body.getReader==="function"){var reader=response.body.getReader(),chunks=[],total=0;while(total<131072){var part=await reader.read();if(part&&part.value){chunks.push(part.value);total+=part.value.byteLength||part.value.length||0}if(!part||part.done)break}try{if(typeof reader.cancel==="function")await reader.cancel()}catch(_e){}var merged=new Uint8Array(total),offset=0;for(var i=0;i<chunks.length;i++){var value=chunks[i],take=Math.min(value.byteLength||value.length||0,total-offset);merged.set(value.subarray?value.subarray(0,take):value,offset);offset+=take;if(offset>=total)break}return clean(new TextDecoder("utf-8").decode(merged))}}catch(_e){}
    return "";
  }
  function playlistKind(body){
    var text=clean(body);if(!/^#EXTM3U(?:\s|$)/i.test(text))return "invalid";
    if(/#EXT-X-STREAM-INF\s*:/i.test(text))return "master";
    if(/#EXTINF\s*:/i.test(text)||/#EXT-X-PART\s*:/i.test(text)||/#EXT-X-MAP\s*:/i.test(text)){
      var lines=text.split(/\r?\n/).map(function(v){return v.trim()}).filter(Boolean);
      if(lines.some(function(v){return v.charAt(0)!=="#"}))return "media";
    }
    return "header_only";
  }
  function variantUris(body,base){
    var lines=clean(body).split(/\r?\n/),out=[];
    for(var i=0;i<lines.length;i++){
      if(!/^#EXT-X-STREAM-INF\s*:/i.test(lines[i]))continue;
      for(var j=i+1;j<lines.length;j++){
        var candidate=clean(lines[j]);if(!candidate)continue;if(candidate.charAt(0)==="#")continue;
        var u=absolute(candidate,base);if(u&&out.indexOf(u)<0)out.push(u);break;
      }
      if(out.length>=config.maxChildren)break;
    }
    return out;
  }
  function audioUris(body,base){
    var out=[],lines=clean(body).split(/\r?\n/);
    lines.forEach(function(line){
      if(!/^#EXT-X-MEDIA\s*:/i.test(line)||!/TYPE\s*=\s*AUDIO/i.test(line))return;
      var m=line.match(/URI\s*=\s*"([^"]+)"/i)||line.match(/URI\s*=\s*([^,\s]+)/i);
      var u=m&&absolute(m[1],base);if(u&&out.indexOf(u)<0)out.push(u);
    });
    return out.slice(0,config.maxChildren);
  }
  async function validateChild(url,stream,referer){
    var result=await fetchBounded(url,stream,referer,false);if(result.state!=="ok")return result.state;
    var body=await responseText(result),kind=playlistKind(body);return kind==="media"||kind==="master"?"valid":"invalid";
  }
  async function inspectHls(url,stream,referer){
    var result=await fetchBounded(url,stream,referer,false);
    if(result.state!=="ok")return {state:result.state,reason:result.reason||"fetch_failed",result:result};
    var ct=result.contentType||"";
    if(/^video\//i.test(ct))return {state:"direct",format:ct.indexOf("webm")>=0?"webm":"mp4",url:result.url,result:result};
    var body=await responseText(result),kind=playlistKind(body);
    if(kind==="invalid"||kind==="header_only")return {state:"invalid",kind:kind,body:body,result:result};
    if(kind==="media")return {state:"valid",kind:kind,url:result.url,body:body,result:result};

    var variants=variantUris(body,result.url||url),audio=audioUris(body,result.url||url);
    if(!variants.length)return {state:"invalid",kind:"master_without_variants",body:body,result:result};
    var variantState="invalid";
    for(var i=0;i<variants.length;i++){
      var s=await validateChild(variants[i],stream,result.url||referer);if(s==="valid"){variantState="valid";break}if(s==="unknown")variantState="unknown";
    }
    if(variantState!=="valid")return {state:variantState,kind:"master_child_"+variantState,body:body,result:result};
    if(audio.length){
      var audioState="invalid";
      for(var j=0;j<audio.length;j++){
        var a=await validateChild(audio[j],stream,result.url||referer);if(a==="valid"){audioState="valid";break}if(a==="unknown")audioState="unknown";
      }
      if(audioState!=="valid")return {state:audioState,kind:"audio_child_"+audioState,body:body,result:result};
    }
    return {state:"valid",kind:"master",url:result.url,body:body,result:result};
  }
  function normalizedText(text){
    return clean(text).replace(/\\u002[fF]/g,"/").replace(/\\\//g,"/").replace(/&amp;/g,"&");
  }
  function candidateUrls(text,base){
    var body=normalizedText(text),out=[],seen={};
    function add(raw){
      var value=clean(raw).replace(/^['"]|['"]$/g,"");if(!value||/^javascript:|^data:/i.test(value))return;
      var u=absolute(value,base);if(!/^https?:\/\//i.test(u)||seen[u])return;seen[u]=1;out.push(u);
    }
    var patterns=[
      /(?:src|href|data-src|data-url|data-file|data-player|data-embed|file|source|url|playlist|hls|stream|embedUrl|embed_url)\s*[:=]\s*["']([^"']+)["']/gi,
      /(https?:\/\/[^"'<>\s\\]+)/gi,
      /["']([^"']+\.(?:m3u8|mpd|mp4|mkv|webm)(?:[?#][^"']*)?)["']/gi
    ],m;
    for(var i=0;i<patterns.length&&out.length<config.maxRecoveryCandidates;i++){
      patterns[i].lastIndex=0;while((m=patterns[i].exec(body))!==null&&out.length<config.maxRecoveryCandidates)add(m[1]);
    }
    return out;
  }
  function mediaHint(url){return /\.m3u8(?:[?#]|$)|\/hls2?\//i.test(url)?"hls":/\.mpd(?:[?#]|$)/i.test(url)?"dash":/\.(?:mp4|mkv|webm)(?:[?#]|$)/i.test(url)?"direct":"page"}
  function cloneRecovered(stream,url,format,referer){
    var row=Object.assign({},stream,{url:url}),headers={};
    var src=stream&&stream.headers&&typeof stream.headers==="object"?stream.headers:{};Object.keys(src).forEach(function(k){headers[k]=String(src[k])});
    if(referer){
      var refKey=Object.keys(headers).find(function(k){return k.toLowerCase()==="referer"}),currentRef=refKey?clean(headers[refKey]):"";
      if(!currentRef||currentRef!==clean(referer)){
        Object.keys(headers).forEach(function(k){var lower=k.toLowerCase();if(lower==="referer"||lower==="origin")delete headers[k]});
        headers.Referer=referer;try{headers.Origin=new URL(referer).origin}catch(_e){}
      }
    }
    if(Object.keys(headers).length)row.headers=headers;
    if(format==="hls"){row.type="hls";if("format" in row)row.format="m3u8"}
    else if(format==="dash"){row.type="dash";if("format" in row)row.format="mpd"}
    else if(format){row.type=format;if("format" in row)row.format=format}
    return row;
  }
  async function probeDirect(url,stream,referer){
    var result=await fetchBounded(url,stream,referer,true);if(result.state!=="ok")return null;
    var ct=result.contentType||"";
    if(/^video\//i.test(ct))return cloneRecovered(stream,result.url,ct.indexOf("webm")>=0?"webm":"mp4",referer);
    if(/(?:application\/dash\+xml|application\/xml|text\/xml)/i.test(ct)||/\.mpd(?:[?#]|$)/i.test(result.url)){
      var dash=await responseText(result);if(/<MPD(?:\s|>)/i.test(dash))return cloneRecovered(stream,result.url,"dash",referer);
    }
    if(/mpegurl/i.test(ct)||/\.m3u8(?:[?#]|$)/i.test(result.url)){
      var hls=await inspectHls(result.url,stream,referer);if(hls.state==="valid")return cloneRecovered(stream,hls.url||result.url,"hls",referer);
    }
    return null;
  }
  async function recover(stream,inspection){
    var queue=[],seen={},pages=0;
    function enqueue(url,referer){var u=absolute(url,referer||String(stream.url||""));if(!/^https?:\/\//i.test(u)||seen[u]||u===String(stream.url||""))return;seen[u]=1;queue.push({url:u,referer:referer||""})}
    var base=inspection&&inspection.result&&inspection.result.url||String(stream.url||"");
    candidateUrls(inspection&&inspection.body||"",base).forEach(function(u){enqueue(u,base)});
    var outerReferer=headerValue(stream,"referer");
    [stream&&stream.playerUrl,stream&&stream.embedUrl,stream&&stream.pageUrl,stream&&stream.sourceUrl,stream&&stream.referrer,stream&&stream.referer].forEach(function(u){if(u)enqueue(u,outerReferer||base)});
    if(outerReferer)enqueue(outerReferer,"");
    while(queue.length&&pages<config.maxRecoveryPages){
      var item=queue.shift(),kind=mediaHint(item.url);
      if(kind==="hls"){
        var hls=await inspectHls(item.url,stream,item.referer);if(hls.state==="valid")return cloneRecovered(stream,hls.url||item.url,"hls",item.referer);if(hls.state==="direct")return cloneRecovered(stream,hls.url||item.url,hls.format||"mp4",item.referer);
        candidateUrls(hls.body||"",hls.result&&hls.result.url||item.url).forEach(function(u){enqueue(u,hls.result&&hls.result.url||item.url)});continue;
      }
      if(kind==="direct"||kind==="dash"){
        var direct=await probeDirect(item.url,stream,item.referer);if(direct)return direct;continue;
      }
      pages++;
      var page=await fetchBounded(item.url,stream,item.referer,false);if(page.state!=="ok")continue;
      var ct=page.contentType||"";
      if(/^video\//i.test(ct))return cloneRecovered(stream,page.url,page.contentType.indexOf("webm")>=0?"webm":"mp4",item.referer);
      var body=await responseText(page);
      if(/^#EXTM3U(?:\s|$)/i.test(body)){
        var pageHls=await inspectHls(page.url,stream,item.referer);if(pageHls.state==="valid")return cloneRecovered(stream,pageHls.url||page.url,"hls",item.referer);
      }
      if(/<MPD(?:\s|>)/i.test(body))return cloneRecovered(stream,page.url,"dash",item.referer);
      candidateUrls(body,page.url||item.url).forEach(function(u){enqueue(u,page.url||item.url)});
    }
    return null;
  }
  async function validateOrRecover(stream){
    var inspection=await inspectHls(String(stream.url||""),stream,headerValue(stream,"referer"));
    if(inspection.state==="valid")return stream;
    if(inspection.state==="unknown"&&!config.failClosedUnknown)return stream;
    if(inspection.state==="direct")return cloneRecovered(stream,inspection.url||String(stream.url||""),inspection.format||"mp4",headerValue(stream,"referer"));
    var recovered=await recover(stream,inspection);if(recovered)return recovered;
    return null;
  }
  async function filterRows(value){
    var rows=Array.isArray(value)?value:value&&Array.isArray(value.streams)?value.streams:null;
    if(!rows)return value;
    var checks=await Promise.all(rows.map(async function(stream){
      if(!config.probeAllUrls&&!hlsHint(stream))return stream;
      var output=await validateOrRecover(stream);
      if(!output){
        try{__nuvioProviderSilentLog("[Nuvio HLS integrity] rejected malformed playlist after bounded recovery",String(stream&&stream.url||"").slice(0,180))}catch(_e){}
      }
      return output;
    }));
    var filtered=checks.filter(Boolean);
    if(Array.isArray(value))return filtered;
    var copy=Object.assign({},value);copy.streams=filtered;return copy;
  }
  function wrap(target,key){
    if(!target||typeof target[key]!=="function"||target[key].__nuvioHlsIntegrityV1)return false;
    var native=target[key];
    var wrapped=async function(){return filterRows(await native.apply(this,arguments))};
    try{Object.defineProperty(wrapped,"__nuvioHlsIntegrityV1",{value:true})}catch(_e){wrapped.__nuvioHlsIntegrityV1=true}
    target[key]=wrapped;return true;
  }
  function install(){
    var done=false;
    try{done=wrap(g,"getStreams")||done}catch(_e){}
    try{if(typeof module!=="undefined"&&module&&module.exports){done=wrap(module.exports,"getStreams")||done;done=wrap(module.exports,"streams")||done}}catch(_e){}
    try{if(typeof exports!=="undefined")done=wrap(exports,"getStreams")||done}catch(_e){}
    return done;
  }
  install();
})(typeof globalThis!=="undefined"?globalThis:this,{"timeoutMs":6500,"maxChildren":2,"maxRecoveryPages":4,"maxRecoveryCandidates":12,"implementationRevision":"recovery-first-v4-timer-safe"});
/* NUVIO_GLOBAL_PROVIDER_SECURITY_HOOK_V1 */
globalThis.__nuvioGlobalProviderSecurityBoundaryV1=true;
/* NUVIO_GLOBAL_STREAM_FACTS_V1:3f39765bf864 */
;(function(g){"use strict";
function s(v){return String(v==null?"":v).trim()}
function meaningful(v){var x=s(v);return x&&!/^(?:unknown|inconnue?|n\/?a|null|undefined|none|-+)$/i.test(x)}
function slot(v){if(Array.isArray(v))return{key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return{key:k,list:v[k]}}}return null}
function rebuild(v,x,list){if(x.key===null)return list;var o=Object.assign({},v);o[x.key]=list;return o}
function blob(row){return [row&&row.name,row&&row.title,row&&row.size,row&&row.description,row&&row.quality,row&&row.language,row&&row.codec,row&&row.audio,row&&row.sourceType,row&&row.releaseType,row&&row.format,row&&row.hdr,row&&row.videoTech,row&&row.bitDepth,row&&row.subtitles].map(s).join(" ")}
function quality(row,b){if(meaningful(row.quality)){var v=s(row.quality);return /^(?:4k|2160p)$/i.test(v)?"2160p":v}var u=b.toUpperCase();if(/(?:\b4K\b|\b2160P?\b|\bUHD\b)/.test(u))return"2160p";var m=u.match(/\b(1440|1080|720|576|540|480|360)P?\b/);return m?m[1]+"p":""}
function language(row,b){if(meaningful(row.language))return s(row.language);var u=b.toUpperCase();if(/\bMULTI(?:[- ]?AUDIO|LANG(?:UE)?S?)?\b/.test(u))return"Multi";if(/\bDUAL(?:[- ]?AUDIO)?\b/.test(u))return"Dual Audio";if(/\bVOSTFR\b/.test(u))return"VOSTFR";if(/\bVFQ\b/.test(u))return"VFQ";if(/\bVFF\b/.test(u))return"VFF";if(/\bVF\b/.test(u))return"VF";if(/\bVO\b/.test(u))return"VO";return""}
function codec(row,b){if(meaningful(row.codec))return s(row.codec);var u=b.toUpperCase();if(/\b(?:HEVC|H[ ._-]?265|X265)\b/.test(u))return"HEVC";if(/\bAV1\b/.test(u))return"AV1";if(/\bVP9\b/.test(u))return"VP9";if(/\b(?:AVC|H[ ._-]?264|X264)\b/.test(u))return"AVC";return""}
function audio(row,b){if(meaningful(row.audio))return s(row.audio);var u=b.toUpperCase(),ch="",m=u.match(/\b(7\.1|5\.1|2\.1|2\.0)\b/);if(m)ch=" "+m[1];if(/\b(?:ATMOS|DOLBY ATMOS)\b/.test(u))return"Dolby Atmos"+ch;if(/\bTRUE[ ._-]?HD\b/.test(u))return"TrueHD"+ch;if(/\b(?:E-?AC-?3|DDP|DD\+)\b/.test(u))return"E-AC3"+ch;if(/\bAC-?3\b/.test(u))return"AC3"+ch;if(/\bDTS[: ._-]?X\b/.test(u))return"DTS:X"+ch;if(/\bDTS[- ]?HD\b/.test(u))return"DTS-HD"+ch;if(/\bDTS\b/.test(u))return"DTS"+ch;if(/\bAAC\b/.test(u))return"AAC"+ch;return""}
function duration(row,b){if(typeof row.duration==="number"&&Number.isFinite(row.duration)&&row.duration>0)return row.duration>600?Math.round(row.duration/60):Math.round(row.duration);var direct=s(row.duration),m=direct.match(/(\d{1,4})\s*(?:min|minutes?)\b/i);if(m)return Number(m[1]);var x=b.match(/\b(\d{1,3})\s*(?:min|minutes?)\b/i);return x?Number(x[1]):0}
function sourceType(row,b){if(meaningful(row.sourceType))return s(row.sourceType);var u=b.toUpperCase();if(/\b(?:BLU[- ]?RAY|BDRIP|BRRIP|BDREMUX)\b/.test(u))return"BLU-RAY";if(/\bWEB[- .]?DL\b/.test(u))return"WEB-DL";if(/\bWEB[- .]?RIP\b/.test(u))return"WEBRIP";if(/\bHDTV\b/.test(u))return"HDTV";if(/\bDVD[- .]?RIP\b/.test(u))return"DVD RIP";return""}
function releaseType(row,b){if(meaningful(row.releaseType))return s(row.releaseType);return /\bREMUX\b/i.test(b)?"REMUX":""}
function formatType(row){if(meaningful(row.format))return s(row.format);var u=s(row.url).split(/[?#]/)[0].toLowerCase();if(/\.m3u8$/.test(u))return"HLS";if(/\.mpd$/.test(u))return"DASH";if(/\.mp4$/.test(u))return"MP4";if(/\.mkv$/.test(u))return"MKV";return""}
function facts(row){if(!row||typeof row!=="object")return row;var out=Object.assign({},row),b=blob(row),q=quality(row,b),l=language(row,b),c=codec(row,b),a=audio(row,b),d=duration(row,b),st=sourceType(row,b),rt=releaseType(row,b),f=formatType(row);if(q)out.quality=q;if(l)out.language=l;if(c)out.codec=c;if(a)out.audio=a;if(d)out.duration=d;if(st)out.sourceType=st;if(rt)out.releaseType=rt;if(f)out.format=f;return out}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioGlobalStreamFactsV1)return false;var native=o[k];var wrap=async function(){var v=await native.apply(this,arguments),x=slot(v);return x?rebuild(v,x,x.list.map(facts)):v};wrap.__nuvioGlobalStreamFactsV1=true;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports){ok=install(module.exports,"getStreams")||install(module.exports,"streams")}}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this);
/* NUVIO_GLOBAL_STREAM_IDENTITY_V1:27ecd1221715 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).replace(/\\\//g,"/").trim()}
function norm(v){try{return s(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}catch(_e){return s(v).toLowerCase()}}
function uniq(values){var out=[],seen={};(values||[]).forEach(function(v){var x=s(v),k=norm(x);if(x&&k&&!seen[k]){seen[k]=1;out.push(x)}});return out}
function slot(v){if(Array.isArray(v))return{key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return{key:k,list:v[k]}}}return null}
function rebuild(v,x,list){if(x.key===null)return list;var o=Object.assign({},v);o[x.key]=list;return o}
function req(a){var f=a[0],q=f&&typeof f==="object"&&!Array.isArray(f)?Object.assign({},f):{tmdbId:f,mediaType:a[1],season:a[2],episode:a[3]};var raw=s(q.tmdbId||q.tmdb_id||q.id||f).replace(/^tmdb:/i,"");q.tmdbId=(raw.match(/^\d+/)||[])[0]||"";q.imdbId=s(q.imdbId||q.imdb_id||"").toLowerCase();q.mediaType=s(q.mediaType||q.type||a[1]||"movie").toLowerCase();q.title=s(q.title||q.name||q.label);q.year=Number(q.year||0)||0;q.season=Number(q.season||a[2]||0)||0;q.episode=Number(q.episode||a[3]||0)||0;return q}
function episodic(q){return q.mediaType==="tv"||q.mediaType==="series"||q.mediaType==="anime"}
function kind(q){return episodic(q)?"tv":"movie"}
function nativeFetchBridge(){try{return !!(g&&typeof g.__native_fetch==="function")}catch(_e){return false}}
function signal(){try{if(typeof AbortSignal!=="undefined"&&typeof AbortSignal.timeout==="function")return AbortSignal.timeout(c.tmdbTimeoutMs)}catch(_e){}return null}
async function jsonFetch(url){if(!g||typeof g.fetch!=="function")return null;var nb=nativeFetchBridge(),sig=nb?null:signal();if(!nb&&!sig)return null;var init={headers:{Accept:"application/json"}};if(sig)init.signal=sig;try{var r=await g.fetch(url,init);if(!r||!r.ok)return null;return await r.json()}catch(_e){return null}}
async function tmdb(q){var titles=uniq([q.title]),episodeTitles=[],year=q.year,imdb=q.imdbId;if(!/^\d+$/.test(q.tmdbId||""))return{titles:titles,episodeTitles:episodeTitles,year:year,imdbId:imdb};var k=kind(q),base="https://api.themoviedb.org/3/"+k+"/"+encodeURIComponent(q.tmdbId),d=await jsonFetch(base+"?api_key="+encodeURIComponent(c.tmdbKey)+"&language=fr-FR&append_to_response=external_ids");if(d){var date=s(d.release_date||d.first_air_date);titles=uniq(titles.concat([d.title,d.name,d.original_title,d.original_name]));year=year||Number((date.match(/(?:19|20)\d{2}/)||[])[0]||0)||0;imdb=imdb||s(d.external_ids&&d.external_ids.imdb_id).toLowerCase()}if(episodic(q)&&q.season>0&&q.episode>0){var epBase=base+"/season/"+encodeURIComponent(q.season)+"/episode/"+encodeURIComponent(q.episode)+"?api_key="+encodeURIComponent(c.tmdbKey)+"&language=";var eps=await Promise.all([jsonFetch(epBase+"fr-FR"),jsonFetch(epBase+"en-US")]);eps.forEach(function(ep){if(ep)episodeTitles=uniq(episodeTitles.concat([ep.name,ep.original_name]))})}return{titles:titles,episodeTitles:episodeTitles,year:year,imdbId:imdb}}
function episode(v){return/(?:^|\D)s(?:eason|aison)?\s*0*(\d{1,3})\s*[-_. ]*e(?:p(?:isode)?)?\s*0*(\d{1,4})(?:\D|$)/i.exec(v)||/(?:season|saison)\s*0*(\d{1,3})[^\d]{0,12}(?:episode|ep)\s*0*(\d{1,4})/i.exec(v)}
function explicitIds(row){var out={tmdbId:"",imdbId:""};var tv=s(row&&(row.tmdbId||row.tmdb_id||row.tmdb));if(/^\d+$/.test(tv))out.tmdbId=tv;var iv=s(row&&(row.imdbId||row.imdb_id||row.imdb)).toLowerCase();if(/^tt\d+$/.test(iv))out.imdbId=iv;try{var u=new URL(s(row&&row.url)),qp=u.searchParams,t=s(qp.get("tmdbId")||qp.get("tmdb")||"");if(!out.tmdbId&&/^\d+$/.test(t))out.tmdbId=t;var i=s(qp.get("imdbId")||qp.get("imdb")||"").toLowerCase();if(!out.imdbId&&/^tt\d+$/.test(i))out.imdbId=i}catch(_e){}return out}
function tokens(v){var noise={the:1,a:1,an:1,le:1,la:1,les:1,un:1,une:1,de:1,des:1,du:1,and:1,et:1,film:1,movie:1,episode:1,season:1,saison:1,stream:1,streaming:1,source:1,server:1,serveur:1,player:1,video:1,watch:1,play:1,direct:1,download:1,quality:1,unknown:1,fallback:1};var tech={vcloud:1,hubcloud:1,file:1,web:1,dl:1,webrip:1,webdl:1,bluray:1,remux:1,hdr:1,dv:1,dolby:1,atmos:1,aac:1,ac3:1,eac3:1,ddp:1,x264:1,x265:1,h264:1,h265:1,hevc:1,av1:1,multi:1,vf:1,vff:1,vfq:1,vostfr:1,vo:1,french:1,english:1,truefrench:1,hd:1,uhd:1,fhd:1,sd:1};var provider=norm(c.providerId).split(" ");return norm(v).split(" ").filter(function(x){return x.length>1&&!noise[x]&&!tech[x]&&provider.indexOf(x)<0&&!/^\d{4}$/.test(x)&&!/^\d{3,4}p$/.test(x)&&!/^s\d+e\d+$/.test(x)})}
function expectedTokens(m){var map={};uniq((m.titles||[]).concat(m.episodeTitles||[])).forEach(function(t){tokens(t).forEach(function(x){map[x]=1})});return map}
function overlapsExpected(text,expected){var w=tokens(text);for(var i=0;i<w.length;i++)if(expected[w[i]])return true;return false}
function explicitCandidates(row){var out=[],title=s(row&&row.title);if(title)out.push({text:title,kind:"title"});var filename=s(row&&row.filename);if(filename)out.push({text:filename,kind:"filename"});try{var base=decodeURIComponent(new URL(s(row&&row.url)).pathname.split("/").filter(Boolean).pop()||"").replace(/\.(?:m3u8|mpd|mp4|mkv|webm|m4v|ts)$/i,"");if(base)out.push({text:base,kind:"url"})}catch(_e){}var name=s(row&&row.name);if(name&&norm(name)!==norm(c.providerId))out.push({text:name,kind:"name"});return out}
function contentLike(candidate){var w=tokens(candidate.text),se=episode(candidate.text),years=norm(candidate.text).match(/\b(?:19|20)\d{2}\b/g)||[];if(se)return true;if(years.length&&w.length>=1)return true;if((candidate.kind==="title"||candidate.kind==="filename")&&w.length>=3)return true;return false}
function queryTitle(text){return tokens(text).join(" ").trim()}
function strongNameMatch(query,result){var a=tokens(query),names=uniq([result&&result.name,result&&result.original_name,result&&result.title,result&&result.original_title]);if(a.length<2)return false;for(var n=0;n<names.length;n++){var b=tokens(names[n]);if(!b.length)continue;var hit=0;a.forEach(function(x){if(b.indexOf(x)>=0)hit++});var ratio=hit/Math.max(a.length,b.length);if(ratio>=0.67)return true}return false}
async function confirmOtherTitle(candidate,q){if(!/^\d+$/.test(q.tmdbId||""))return false;var query=queryTitle(candidate.text);if(tokens(query).length<2)return false;var endpoint=episodic(q)?"tv":"movie",d=await jsonFetch("https://api.themoviedb.org/3/search/"+endpoint+"?api_key="+encodeURIComponent(c.tmdbKey)+"&language=fr-FR&query="+encodeURIComponent(query)+"&include_adult=false");if(!d||!Array.isArray(d.results))return false;for(var i=0;i<Math.min(5,d.results.length);i++){var row=d.results[i];if(!strongNameMatch(query,row))continue;var id=s(row&&row.id);if(id===q.tmdbId)return false;return /^\d+$/.test(id)&&id!==q.tmdbId}return false}
async function candidateContradicts(candidate,q,m,expected){var text=candidate.text,se=episode(text);if(q.mediaType==="movie"&&se)return true;if(se&&episodic(q)){var ss=Number(se[1])||0,ee=Number(se[2])||0;if((q.season&&ss&&ss!==q.season)||(q.episode&&ee&&ee!==q.episode))return true;if(overlapsExpected(text,expected))return false;return await confirmOtherTitle(candidate,q)}var years=norm(text).match(/\b(?:19|20)\d{2}\b/g)||[];if(m.year&&years.length&&!years.some(function(y){return Math.abs(Number(y)-Number(m.year))<=1}))return true;if(!contentLike(candidate)||overlapsExpected(text,expected))return false;var w=tokens(text);if(w.length<2)return false;if(years.length)return true;if(w.length>=3&&(candidate.kind==="title"||candidate.kind==="filename"))return await confirmOtherTitle(candidate,q);return false}
async function mismatch(row,q,m){var ids=explicitIds(row);if(ids.tmdbId&&q.tmdbId&&ids.tmdbId!==q.tmdbId)return true;if(ids.imdbId&&(q.imdbId||m.imdbId)&&ids.imdbId!==(q.imdbId||m.imdbId))return true;var expected=expectedTokens(m),cands=explicitCandidates(row);for(var i=0;i<cands.length;i++)if(await candidateContradicts(cands[i],q,m,expected))return true;return false}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioGlobalStreamIdentityV1)return false;var native=o[k];var wrap=async function(){var q=req(arguments),v=await native.apply(this,arguments),x=slot(v);if(!x||!x.list.length)return v;var m=await tmdb(q),kept=[];for(var i=0;i<x.list.length;i++)if(!(await mismatch(x.list[i],q,m)))kept.push(x.list[i]);return rebuild(v,x,kept)};wrap.__nuvioGlobalStreamIdentityV1=true;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports){ok=install(module.exports,"getStreams")||install(module.exports,"streams")}}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,{"providerId":"animezey","tmdbKey":"1865f43a0549ca50d341dd9ab8b29f49","tmdbTimeoutMs":1200,"implementationRevision":"cross-client-positive-mismatch-anime-confirmed-v3"});
/* NUVIO_GLOBAL_STREAM_PRESENTATION_V1:5bcd7b6dd2c2 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function meaningful(v){var x=s(v);return x&&!/^(?:unknown|inconnue?|n\/?a|null|undefined|none|-+)$/i.test(x)}
function uniq(a){var o=[];(a||[]).forEach(function(v){if(v&&o.indexOf(v)<0)o.push(v)});return o}
function slot(v){if(Array.isArray(v))return{key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return{key:k,list:v[k]}}}return null}
function rebuild(v,x,list){if(x.key===null)return list;var o=Object.assign({},v);o[x.key]=list;return o}
function req(a){var f=a[0],q=f&&typeof f==="object"&&!Array.isArray(f)?Object.assign({},f):{tmdbId:f,mediaType:a[1],season:a[2],episode:a[3]};q.tmdbId=s(q.tmdbId||q.id||f).replace(/^tmdb:/i,"").split(":")[0];q.mediaType=s(q.mediaType||q.type||a[1]||"movie").toLowerCase();q.title=s(q.title||q.name||q.label);q.year=Number(q.year||0)||0;q.season=Number(q.season||a[2]||0)||0;q.episode=Number(q.episode||a[3]||0)||0;return q}
function blob(r){return [r&&r.name,r&&r.title,r&&r.size,r&&r.description,r&&r.quality,r&&r.language,r&&r.codec,r&&r.audio,r&&r.sourceType,r&&r.releaseType,r&&r.format,r&&r.hdr,r&&r.videoTech,r&&r.bitDepth,r&&r.subtitles].map(s).join(" ")}
function quality(r){var v=meaningful(r&&r.quality)?s(r.quality):blob(r),u=v.toUpperCase();if(/(?:\b4K\b|\b2160P?\b|\bUHD\b)/.test(u))return"2160p";var m=u.match(/\b(1440|1080|720|576|540|480|360)P?\b/);return m?m[1]+"p":""}
function language(r){var v=meaningful(r&&r.language)?s(r.language):blob(r),u=v.toUpperCase();if(/\bMULTI(?:[- ]?AUDIO|LANG(?:UE)?S?)?\b/.test(u))return"Multi";if(/\bDUAL(?:[- ]?AUDIO)?\b/.test(u))return"Dual Audio";if(/\bVOSTFR\b/.test(u))return"VOSTFR";if(/\bVFQ\b/.test(u))return"VFQ";if(/\bVFF\b/.test(u))return"VFF";if(/\bVF\b/.test(u))return"VF";if(/\bVO\b/.test(u))return"VO";return meaningful(r&&r.language)?s(r.language):""}
function codec(r){var v=meaningful(r&&r.codec)?s(r.codec):blob(r),u=v.toUpperCase();if(/\b(?:HEVC|H[ ._-]?265|X265)\b/.test(u))return"HEVC";if(/\bAV1\b/.test(u))return"AV1";if(/\bVP9\b/.test(u))return"VP9";if(/\b(?:AVC|H[ ._-]?264|X264)\b/.test(u))return"AVC";return meaningful(r&&r.codec)?s(r.codec):""}
function audio(r){var v=meaningful(r&&r.audio)?s(r.audio):blob(r),u=v.toUpperCase(),ch="",cm=u.match(/\b(7\.1|5\.1|2\.1|2\.0)\b/);if(cm)ch=cm[1];var fmt="";if(/\b(?:ATMOS|DOLBY ATMOS)\b/.test(u))fmt="Dolby Atmos";else if(/\bTRUE[ ._-]?HD\b/.test(u))fmt="TrueHD";else if(/\b(?:E-?AC-?3|DDP|DD\+)\b/.test(u))fmt="E-AC3";else if(/\bAC-?3\b/.test(u))fmt="AC3";else if(/\bDTS[: ._-]?X\b/.test(u))fmt="DTS:X";else if(/\bDTS[- ]?HD\b/.test(u))fmt="DTS-HD";else if(/\bDTS\b/.test(u))fmt="DTS";else if(/\bAAC\b/.test(u))fmt="AAC";return{format:fmt||(meaningful(r&&r.audio)?s(r.audio):""),channels:ch}}
function duration(r){var raw=r&&r.duration;if(typeof raw==="number"&&Number.isFinite(raw)&&raw>0)return raw>600?Math.round(raw/60):Math.round(raw);var d=s(raw),m=d.match(/(\d{1,4})\s*(?:min|minutes?)\b/i);if(m)return Number(m[1]);var x=blob(r).match(/\b(\d{1,3})\s*(?:min|minutes?)\b/i);return x?Number(x[1]):0}
function source(r){var v=meaningful(r&&r.sourceType)?s(r.sourceType):blob(r),u=v.toUpperCase(),sourceType="",releaseType="";if(/\b(?:BLU[- ]?RAY|BDRIP|BRRIP|BDREMUX)\b/.test(u))sourceType="BLU-RAY";else if(/\bWEB[- .]?DL\b/.test(u))sourceType="WEB-DL";else if(/\bWEB[- .]?RIP\b/.test(u))sourceType="WEBRIP";else if(/\bHDTV\b/.test(u))sourceType="HDTV";else if(/\bDVD[- .]?RIP\b/.test(u))sourceType="DVD RIP";if(/\bREMUX\b/.test(u))releaseType="REMUX";return{sourceType:sourceType||(meaningful(r&&r.sourceType)?s(r.sourceType):""),releaseType:releaseType||(meaningful(r&&r.releaseType)?s(r.releaseType):"")}}
function formatType(r){var v=meaningful(r&&r.format)?s(r.format):"",u=v.toUpperCase();if(/(?:M3U8|HLS)/.test(u))return"HLS";if(/(?:MPD|DASH)/.test(u))return"DASH";if(/\bMP4\b/.test(u))return"MP4";if(/\bMKV\b/.test(u))return"MKV";var url=s(r&&r.url).split(/[?#]/)[0].toLowerCase();if(/\.m3u8$/.test(url))return"HLS";if(/\.mpd$/.test(url))return"DASH";if(/\.mp4$/.test(url))return"MP4";if(/\.mkv$/.test(url))return"MKV";return v}
function videoFacts(r){var u=blob(r).toUpperCase(),tech=[],bit="";if(/\b(?:DOLBY VISION|DOVI)\b/.test(u))tech.push("Dolby Vision");if(/\bHDR10\+\b|\bHDR10 PLUS\b/.test(u))tech.push("HDR10+");else if(/\bHDR10\b/.test(u))tech.push("HDR10");if(/\bIMAX[ ._-]?ENHANCED\b/.test(u))tech.push("IMAX Enhanced");else if(/\bIMAX\b/.test(u))tech.push("IMAX");if(/\b10[ ._-]?BIT\b|\bHI10P\b/.test(u))bit="10bit";else if(/\b8[ ._-]?BIT\b/.test(u))bit="8bit";return{tech:uniq(tech),bitDepth:bit}}
function subtitleFacts(r){var u=blob(r).toUpperCase(),out=[];if(/\bVOSTFR\b/.test(u))out.push("VOSTFR");if(/\bSUB[ ._-]?FR\b/.test(u))out.push("SUB FR");if(/\bSUB[ ._-]?EN\b/.test(u))out.push("SUB EN");if(/\bFORCED\b/.test(u))out.push("FORCED");if(/\bSDH\b/.test(u))out.push("SDH");return uniq(out)}
function age(r){var v=r&&(r.ageRating||r.certification);return meaningful(v)?s(v):""}
function providerName(r){var raw=meaningful(r&&r.name)?s(r.name):"",n=raw.split(/[|\n]/)[0].trim();if(n&&n.length<=40&&!/^(?:4k|2160p|1080p|720p|vf|vff|vfq|vostfr)$/i.test(n))return n;var id=s(c.providerId).replace(/[-_]+/g," ");return id?id.replace(/\b\w/g,function(x){return x.toUpperCase()}):"Source"}
function fileSize(r){var v=s(r&&r.size);if(!meaningful(v))return"";return /\b\d+(?:[.,]\d+)?\s*(?:KB|MB|GB|TB)\b/i.test(v)?v:""}
function badgeIds(f){var ids=[];var q={"2160p":"4k-ultra-hd","1080p":"1080p-full-hd","720p":"720p-hd","480p":"480p-sd"}[f.quality];if(q)ids.push(q);var src={"BLU-RAY":"blu-ray-disc","WEB-DL":"webdl","WEBRIP":"webrip","HDTV":"hdtv","DVD RIP":"dvd-rip"}[f.sourceType];if(src)ids.push(src);if(f.releaseType==="REMUX")ids.push("remux");f.videoTech.forEach(function(v){var id={"Dolby Vision":"dolby-vision","HDR10+":"hdr10-plus","HDR10":"hdr10","IMAX Enhanced":"imax-enhanced","IMAX":"imax"}[v];if(id)ids.push(id)});var co={"HEVC":"hevc","AVC":"avc"}[f.codec];if(co)ids.push(co);if(f.bitDepth)ids.push(f.bitDepth);var af={"Dolby Atmos":"dolby-atmos","TrueHD":"truehd","E-AC3":"dolby-digital-plus","AC3":"dolby-digital","DTS:X":"dts-x","DTS-HD":"dts-hd-master-audio"}[f.audioFormat];if(af)ids.push(af);if(f.audioChannels==="7.1")ids.push("7.1");else if(f.audioChannels==="5.1")ids.push("5.1");var lg={"Multi":"multi","VFF":"vff","VFQ":"vfq","VO":"vo","VOSTFR":"vostfr"}[f.language];if(lg)ids.push(lg);f.subtitles.forEach(function(v){var id={"VOSTFR":"vostfr","SUB FR":"sub-fr","SUB EN":"sub-en","FORCED":"forced","SDH":"sdh-cc"}[v];if(id)ids.push(id)});return uniq(ids)}
function badgeLabels(f){var out=[];if(f.quality)out.push(f.quality==="2160p"?"4K":f.quality);if(f.sourceType)out.push(f.sourceType);if(f.releaseType)out.push(f.releaseType);out=out.concat(f.videoTech);if(f.codec)out.push(f.codec);if(f.bitDepth)out.push(f.bitDepth);if(f.audioFormat)out.push(f.audioFormat);if(f.audioChannels)out.push(f.audioChannels);if(f.language)out.push(f.language);out=out.concat(f.subtitles);if(f.duration)out.push(Math.floor(f.duration/60)?Math.floor(f.duration/60)+"h"+String(f.duration%60).padStart(2,"0"):f.duration+"min");if(f.ageRating)out.push(f.ageRating);return uniq(out)}
function nativeFetchBridge(){try{return !!(g&&typeof g.__native_fetch==="function")}catch(_e){return false}}
function safeSignal(){try{if(typeof AbortSignal!=="undefined"&&typeof AbortSignal.timeout==="function")return AbortSignal.timeout(c.tmdbTimeoutMs)}catch(_e){}return null}
function certification(d,kind){var rows=kind==="movie"?(d&&d.release_dates&&d.release_dates.results):(d&&d.content_ratings&&d.content_ratings.results);if(!Array.isArray(rows))return"";var row=rows.find(function(x){return s(x&&x.iso_3166_1).toUpperCase()==="FR"})||rows.find(function(x){return s(x&&x.iso_3166_1).toUpperCase()==="US"})||rows[0];if(!row)return"";if(kind==="movie"){var releases=Array.isArray(row.release_dates)?row.release_dates:[];for(var i=0;i<releases.length;i++){var v=s(releases[i]&&releases[i].certification);if(v)return v}return""}return s(row.rating)}
async function tmdbJson(url){if(!g||typeof g.fetch!=="function")return null;var nativeBridge=nativeFetchBridge(),sig=nativeBridge?null:safeSignal();if(!nativeBridge&&!sig)return null;var init={headers:{Accept:"application/json"}};if(sig)init.signal=sig;try{var r=await g.fetch(url,init);if(!r||!r.ok)return null;return await r.json()}catch(_e){return null}}
async function tmdb(q){if(!/^\d+$/.test(q.tmdbId||""))return null;var kind=(q.mediaType==="tv"||q.mediaType==="series"||q.mediaType==="anime")?"tv":"movie",append=kind==="movie"?"release_dates":"content_ratings",base="https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(q.tmdbId),d=await tmdbJson(base+"?api_key="+encodeURIComponent(c.tmdbKey)+"&language=fr-FR&append_to_response="+append);if(!d)return null;var date=s(d.release_date||d.first_air_date),runtime=Number(d.runtime||0);if(!runtime&&Array.isArray(d.episode_run_time)&&d.episode_run_time.length)runtime=Number(d.episode_run_time[0]||0);var genres=Array.isArray(d.genres)?d.genres.map(function(x){return s(x&&x.name)}).filter(Boolean):[];var meta={title:s(d.title||d.name||q.title),year:Number((date.match(/(?:19|20)\d{2}/)||[])[0]||q.year||0)||0,runtime:runtime>0?Math.round(runtime):0,age:certification(d,kind),overview:s(d.overview),genres:genres,episodeTitle:"",episodeOverview:""};if(kind==="tv"&&q.season>0&&q.episode>0){var ep=await tmdbJson(base+"/season/"+encodeURIComponent(q.season)+"/episode/"+encodeURIComponent(q.episode)+"?api_key="+encodeURIComponent(c.tmdbKey)+"&language=fr-FR");if(ep){var er=Number(ep.runtime||0);if(er>0)meta.runtime=Math.round(er);meta.episodeTitle=s(ep.name);meta.episodeOverview=s(ep.overview)}}return meta}
function mediaLine(meta,q){var title=s((meta&&meta.title)||q.title),year=Number((meta&&meta.year)||q.year||0)||0,parts=[];if(title)parts.push(title);if(year)parts.push(String(year));if((q.mediaType==="tv"||q.mediaType==="series"||q.mediaType==="anime")&&(q.season>0||q.episode>0)){parts.push("S"+String(q.season||0).padStart(2,"0")+"E"+String(q.episode||0).padStart(2,"0"));if(meta&&meta.episodeTitle)parts.push(meta.episodeTitle)}return parts.join(" • ")}
function compact(meta,q){var title=s((meta&&meta.title)||q.title),parts=[];if(title)parts.push(title);if((q.mediaType==="tv"||q.mediaType==="series"||q.mediaType==="anime")&&(q.season>0||q.episode>0))parts.push("S"+String(q.season||0).padStart(2,"0")+"E"+String(q.episode||0).padStart(2,"0"));return parts.join(" • ")}
function present(r,meta,q){if(!r||typeof r!=="object")return r;var out=Object.assign({},r),au=audio(r),so=source(r),vf=videoFacts(r),f={quality:quality(r),language:language(r),codec:codec(r),audioFormat:au.format,audioChannels:au.channels,duration:duration(r)||(meta&&meta.runtime)||0,sourceType:so.sourceType,releaseType:so.releaseType,format:formatType(r),videoTech:vf.tech,bitDepth:vf.bitDepth,subtitles:subtitleFacts(r),ageRating:age(r)||(meta&&meta.age)||""};if(f.quality)out.quality=f.quality;if(f.language)out.language=f.language;if(f.codec)out.codec=f.codec;if(f.audioFormat)out.audio=f.audioFormat+(f.audioChannels?" "+f.audioChannels:"");if(f.duration)out.duration=f.duration;if(f.sourceType)out.sourceType=f.sourceType;if(f.releaseType)out.releaseType=f.releaseType;if(f.format)out.format=f.format;if(f.ageRating)out.ageRating=f.ageRating;out.badgeIds=badgeIds(f);out.displayBadges=badgeLabels(f);out.presentationFacts=f;var provider=providerName(r),media=mediaLine(meta,q),small=compact(meta,q),genres=meta&&Array.isArray(meta.genres)&&meta.genres.length?meta.genres.slice(0,3).join(", "):"",overview=s(meta&&((meta.episodeOverview)||meta.overview)),lines=[];if(media)lines.push(((q.mediaType==="tv"||q.mediaType==="series"||q.mediaType==="anime")?"📺 ":"🎬 ")+media+(genres?" • "+genres:""));if(overview)lines.push(overview);if(!lines.length)lines.push("🎬 "+provider);out.title=small?provider+" • "+small:provider;out.name=provider;out.description=lines.join("\n");var fs=fileSize(r);if(fs)out.size=fs;else if("size" in out)delete out.size;return out}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioGlobalStreamPresentationV1)return false;var native=o[k];var wrap=async function(){var q=req(arguments),v=await native.apply(this,arguments),x=slot(v);if(!x||!x.list.length)return v;var meta=null;try{meta=await tmdb(q)}catch(_e){}return rebuild(v,x,x.list.map(function(r){return present(r,meta,q)}))};wrap.__nuvioGlobalStreamPresentationV1=true;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports){ok=install(module.exports,"getStreams")||install(module.exports,"streams")}}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,{"providerId":"animezey","tmdbKey":"1865f43a0549ca50d341dd9ab8b29f49","tmdbTimeoutMs":1200,"implementationRevision":"all-providers-facts-badge-dedupe-tmdb-fallback-v10"});
/* NUVIO_GLOBAL_PROVIDER_BRANDING_V1:9b1b6c70b808 */
;(function(g,c){"use strict";
function slot(v){if(Array.isArray(v))return{key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return{key:k,list:v[k]}}}return null}
function rebuild(v,x,list){if(x.key===null)return list;var o=Object.assign({},v);o[x.key]=list;return o}
function label(){return(String(c.providerEmoji||"").trim()+" "+String(c.providerName||c.providerId||"Source").trim()).trim()}
function title(v,old){old=String(old||"").trim();if(!old)return v;var token=" • ",i=old.indexOf(token);return i>=0?v+old.slice(i):v}
function brand(r){if(!r||typeof r!=="object")return r;var o=Object.assign({},r),v=label();if(!v)return o;o.title=title(v,o.title);o.name=v;return o}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioGlobalProviderBrandingV1)return false;var native=o[k];var wrap=async function(){var v=await native.apply(this,arguments),x=slot(v);if(!x||!x.list.length)return v;return rebuild(v,x,x.list.map(brand))};wrap.__nuvioGlobalProviderBrandingV1=true;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports){ok=install(module.exports,"getStreams")||install(module.exports,"streams")}}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,{"providerId":"animezey","providerName":"AnimeZeY","providerEmoji":"🌀","implementationRevision":"post-presentation-emoji-stream-label-v4"});
