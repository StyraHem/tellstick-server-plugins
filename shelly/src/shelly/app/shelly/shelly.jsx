define(
  ['react', 'react-mdl', 'react-router', 'websocket'],
  function(React, ReactMDL, ReactRouter, WebSocket) {
    class ShellyApp extends React.Component {
      constructor(props) {
		super(props);
		this.state = {'devices': null}
		this.websocket = new WebSocket();
	  }
	  componentDidMount() {
	  	this.websocket.onMessage('shelly', 'refresh', (module, action, data) => this.setState(data));
	  	fetch('/shelly/list')
	  	  .then(response => response.json())
	  	  .then(json => this.setState({'devices': json.devices, 'ver' : json.ver }))
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
	  rename(id, oldName, e) { 
	      e.preventDefault();
	      var newName = prompt("Enter new name", oldName);
	      if (newName != null)
	      	fetch('/shelly/rename?id=' + id + '&name=' + newName)
  	  }
	  render() {
	      const { devices, ver } = this.state;
	  	  if (!devices) {
	  	  	return ( <div></div> )
	  	  }
	      const CanvasStyle:any = {
		   	margin: '5px 10px',
          };
          const UnavailableStyle:any = {
		  	color: 'gray'
          };
          const HideStyle:any = {
		  	visibility: 'hidden'
          };
          const HeadStyle:any = { 
		  	width: '400px'
          };
	      return (
	       <div style={CanvasStyle}>	        
	        <table>
	        	<tr>
	        		<td style={HeadStyle}><h1>Shelly</h1></td>
	        		<td>pyShelly: {ver}</td>
	        	</tr>
	        </table>
	        <ReactMDL.Button onClick={(e) => this.clean(e)}>Clean</ReactMDL.Button>
	        <ReactMDL.Button onClick={(e) => this.discover(e)}>Discover</ReactMDL.Button>
	        <ReactMDL.Button onClick={(e) => this.initSocket(e)}>Init socket</ReactMDL.Button>
	        <ReactMDL.Button onClick={(e) => this.addMember(e)}>Add member</ReactMDL.Button>
	        <ReactMDL.Button onClick={(e) => this.dropMember(e)}>Drop member</ReactMDL.Button>
	      	<table><tbody>
	          {devices.map(dev =>
	            <tr key={dev.id} style={!dev.available ? UnavailableStyle : null}>
	              <td>
	              	{ dev.available &&
	              		<img src={"https://live.telldus.com/img/state/state_" + dev.state[0] + ".png"}></img>
	              	}
	              </td>
	              <td>{dev.name}</td>
	              <td>{dev.ipaddr}</td>
	              <td style={!dev.available ? HideStyle : null}>
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
	       </div>
	      );
  	  }
    };

  return ShellyApp;
  }
);
