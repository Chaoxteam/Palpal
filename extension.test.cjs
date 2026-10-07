const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('extension/worker.js', 'utf8');
function extension(epoch, url='https://youtube.com/watch?v=private', agent='Chrome') {
  const posts=[];let reads=0;
  const event={addListener(){}};
  const context={URL,Date,navigator:{userAgent:agent},chrome:{
    storage:{local:{get:async()=>({token:'local-token'})}},
    windows:{getAll:async()=>[{id:1,focused:true}],onFocusChanged:event},
    tabs:{query:async()=>{reads++;return [{url,title:'Quadratic equations'}];},onActivated:event,onUpdated:event}
  },fetch:async(path,options)=>{
    if(path.endsWith('/status')) return {ok:true,json:async()=>({epoch})};
    posts.push(JSON.parse(options.body));return {ok:true};
  }};
  vm.createContext(context);vm.runInContext(source,context);
  return {report:context.report,posts,reads:()=>reads};
}
test('inactive session reads no tab data',async()=>{
 const app=extension(null);await app.report();assert.equal(app.reads(),0);assert.equal(app.posts.length,0);
});
test('only domain and title are sent, without URL path or query',async()=>{
 const app=extension('session');await app.report();
 assert.equal(app.posts[0].domain,'youtube.com');assert.equal(app.posts[0].browser,'chrome.exe');assert.equal(app.posts[0].url,undefined);
 assert.equal(JSON.stringify(app.posts).includes('private'),false);
});
test('internal pages clear old browser context',async()=>{
 const app=extension('session','chrome://extensions');await app.report();assert.equal(app.posts[0].domain,'');assert.equal(app.posts[0].title,'');
});
test('Edge identifies itself',async()=>{
 const app=extension('session','https://example.org','Chrome Edg/123');await app.report();assert.equal(app.posts[0].browser,'msedge.exe');
});
