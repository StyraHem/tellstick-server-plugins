define(
  ['react', 'react-mdl', 'react-router', 'websocket','telldus'],
  function(React, ReactMDL, ReactRouter, WebSocket, Telldus) {
  
    Telldus.loadCSS('/shelly/style/shelly.css');
    
    class ShellyApp extends React.Component {
      constructor(props) {
        super(props);
        this.state = {'devices': null}
        this.websocket = new WebSocket();
      }
      componentDidMount() {
        this.websocket.onMessage('shelly', 'refresh', (module, action, data) => {
            console.log(data);
            this.setState(data)
        });
        fetch('/shelly/list')
          .then(response => response.json())
          .then(json => this.setState({'devices': json.devices, 'ver' : json.ver, 'pyShellyVer' : json.pyShellyVer }))
      }
      componentWillUnmount() {
        this.websocket.onMessage('shelly', 'status', null);
      }
      sendCmd(id, cmd, e) {
          e.preventDefault();
          fetch('/shelly/' + cmd + '?id=' + id)
      }
      addMember(e) {
          e.preventDefault();
          fetch('/shelly/addMember')
      }
      dropMember(e) {
          e.preventDefault();
          fetch('/shelly/dropMember')
      }
      clean(e) {
          e.preventDefault();
          fetch('/shelly/clean')
      }
      initSocket(e) {
          e.preventDefault();
          fetch('/shelly/initSocket')
      }
      discover(e) {
          e.preventDefault();
          fetch('/shelly/discover')
      }
      pickColor(id, e) {
        this.selectedId = id;
        var pos = this.getPos(e.target);
        
        var canvas = document.getElementById('picker');
        canvas.style.display = "block";
        canvas.style.top = pos[1]-50;
        canvas.style.left = pos[0]-300;
        var ctx = canvas.getContext('2d');       

        var image = new Image();        
        image.onload = function () {
            ctx.drawImage(image, 0, 0, image.width, image.height);
        }
        image.src = "/shelly/img/colorwheel.png"
        
        document.addEventListener('mousedown', this.outsidePick);
      }
      outsidePick(e) {
        var canvas = document.getElementById('picker');
        if (e==null || !canvas.contains(event.target)) {
            document.removeEventListener('mousedown', this.handleClickOutside);
            canvas.style.display = "none"; 
            //this.selectedId = 0;
        }
      }
      getPos(el) {
        var x = 0;
        var y = 0;        
        while( el && !isNaN( el.offsetLeft ) && !isNaN( el.offsetTop ) ) {
            x += el.offsetLeft - el.scrollLeft;
            y += el.offsetTop - el.scrollTop;
            el = el.offsetParent;
        }
        return [x, y]
      }
      //toHex(c) {
      //    var hex = c.toString(16);
      //    return hex.length == 1 ? "0" + hex : hex;
      //} 
      selectColor(e) {
      
        var canvas = document.getElementById('picker');
        var ctx = canvas.getContext('2d');
        
        var pos = this.getPos(e.target);
        
        var canvasX = Math.floor(e.pageX - pos[0]);
        var canvasY = Math.floor(e.pageY - pos[1]);

        // get current pixel
        var imageData = ctx.getImageData(canvasX, canvasY, 1, 1);
        var pixel = imageData.data;

        //this.setState( state => {
        //    state.devices.find(d=>d.id==this.selectedId).changingColorTo 
        //                        = '#'+this.toHex(pixel[0])+this.toHex(pixel[1])+this.toHex(pixel[2])
        //    return {devices: state.devices};
        //});
        
        fetch("/shelly/rgb?id="+this.selectedId+"&r="+pixel[0]+"&g="+pixel[1]+"&b="+pixel[2] )
        this.outsidePick();
      }
      rename(id, oldName, e) { 
          e.preventDefault();
          var newName = prompt("Enter new name", oldName);
          if (newName != null)
            fetch('/shelly/rename?id=' + id + '&name=' + newName)
      }
      renderValues(dev) {
        var values = {};
        if (dev.sensors['watt'])
            values['watt']=dev.sensors['watt'] + "W";
        if (dev.sensors['temp'])
            values['temp']=dev.sensors['temp'] + "\u00B0C";
        if (dev.sensors['hum'])
            values['hum']=dev.sensors['hum'] + "%";
        if (dev.mode!="") {
            if (dev.state[1])
                values['brght']=Math.round(dev.state[1]/2.55) + "%";
            else if (dev.state[0]!=2)
                values['brght']="100%";
        }
        return <div className="values">{Object.entries(values)
                     .map(([key, value])=><span key={key} className="value">{value}</span>)}</div>;
      }
      render() {
          const { devices, ver, pyShellyVer } = this.state;
          return (           
           <div className="shellyCanvas">  
            <table><tbody>
                <tr>
                    <td className="head"></td>
                    <td>Version: {ver}<br/>pyShelly: {pyShellyVer}</td>
                </tr>
            </tbody></table>
            {/*
            <ReactMDL.Button onClick={(e) => this.clean(e)}>Clean</ReactMDL.Button>
            <ReactMDL.Button onClick={(e) => this.discover(e)}>Discover</ReactMDL.Button>
            <ReactMDL.Button onClick={(e) => this.initSocket(e)}>Init socket</ReactMDL.Button>
            <ReactMDL.Button onClick={(e) => this.addMember(e)}>Add member</ReactMDL.Button>
            <ReactMDL.Button onClick={(e) => this.dropMember(e)}>Drop member</ReactMDL.Button>
            */}
            { devices &&
            <table className="list"><tbody>
              <tr><th></th><th></th><th>Name</th><th>Type</th><th>IP address</th><th></th><th></th></tr>
              {devices.map(dev =>
                <tr key={dev.id} className={!dev.available ? "unavailable" : "available"}>                  
                  <td>
                    { dev.available && dev.isDevice &&
                        <img src={"/shelly/img/state_" + dev.state[0] + ".png"}></img>
                    }
                  </td>
                  <td>
                    { dev.available && dev.rgb &&
                        <div onClick={(e) => this.pickColor(dev.id, e)}
                            className="rgb" style={{backgroundColor:dev.rgb}}></div>
                    }
                    { this.renderValues(dev) }
                  </td>
                  <td>{dev.name}</td>
                  <td>{dev.typeName}</td>
                  <td><a href={"http://" + dev.ipaddr} target="_blank">{dev.ipaddr}</a></td>
                  <td className={!dev.available ? "hide" : ""}>
                    { dev.buttons.on &&
                    <ReactMDL.Button onClick={(e) => this.sendCmd(dev.id, "turnon", e)}>Turn on</ReactMDL.Button>}
                    { dev.buttons.off &&
                    <ReactMDL.Button onClick={(e) => this.sendCmd(dev.id, "turnoff", e)}>Turn off</ReactMDL.Button>}
                    { dev.buttons.up &&
                    <ReactMDL.Button onClick={(e) => this.sendCmd(dev.id, "up", e)}>Up</ReactMDL.Button>}
                    { dev.buttons.down &&
                    <ReactMDL.Button onClick={(e) => this.sendCmd(dev.id, "down", e)}>Down</ReactMDL.Button>}
                    { dev.buttons.stop &&
                    <ReactMDL.Button onClick={(e) => this.sendCmd(dev.id, "stop", e)}>Stop</ReactMDL.Button>}
                    </td>
                   <td>
                    <ReactMDL.Button onClick={(e) => this.rename(dev.id, dev.name, e)}>Rename</ReactMDL.Button>
                  </td>
                </tr>
              )}
            </tbody></table>
            }                
            <canvas id="picker" width="300" height="300" onClick={(e) => this.selectColor(e)}></canvas>
           </div>
          );
      }
    };

  return ShellyApp;
  }
);
