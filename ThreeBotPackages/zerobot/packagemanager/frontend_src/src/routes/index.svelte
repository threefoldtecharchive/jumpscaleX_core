
<script>
	import { onMount } from "svelte";

	let method = "path";
	let newPackagePath = "";
	let lastError = null;
	let packages = [];
	const pkgStatus = {
		0: {name: "Init", actions: ["delete"]},
		1: {name: "Installed", actions: ['delete', "start"]},
		2: {name: "Running", actions: ['delete', "stop"]},
		3: {name: "Halted", actions: ['delete', "start", "disable"]},
		4: {name: "Disabled", actions: ['delete', "enable"]},
		5: {name: "Error", actions: ["delete"]}
	}

	onMount(async () => {
		updatePackages()
	});

	function updatePackages() {
		packageGedisClient.zerobot.packagemanager.actors.package_manager.packages_list().then((resp) => {
			if (resp.ok) {
				resp.json().then((data) => {
					packages = data.packages;
					lastError = null;
				})
			} else {
				let err = new Error(resp)
				lastError = err;
				throw err;
			}
		})
	}

	function packageAdd() {
		let args = {};
		args[method] = newPackagePath;
		packageGedisClient.zerobot.packagemanager.actors.package_manager.package_add(args).then((resp) => {
			if(resp.ok) {
				lastError = null;
				updatePackages()
       		} else {
				lastError = "Couldn't add package " + newPackagePath;
			}
		})
	}

	function packageEnable(name) {
		let args = {name: name}
		packageGedisClient.zerobot.packagemanager.actors.package_manager.package_enable(args).then((resp) => {
			if(resp.ok) {
				lastError = null;
				updatePackages()
       		} else {
				lastError = "Couldn't enable package " + name;
			}
		})
	}

	function packageDisable(name) {
		let args = {name: name}
		packageGedisClient.zerobot.packagemanager.actors.package_manager.spackage_disable(args).then((resp) => {
			if(resp.ok) {
				lastError = null;
				updatePackages()
       		} else {
				lastError = "Couldn't disable package " + name;
			}
		})
	}

	function packageStop(name) {
		let args = {name: name}
		packageGedisClient.zerobot.packagemanager.actors.package_manager.package_stop(args).then((resp) => {
			if(resp.ok) {
				lastError = null;
				updatePackages()
       		} else {
				lastError = "Couldn't stop package " + name;
			}
		})
	}

	function packageStart(name) {
		let args = {name: name}
		packageGedisClient.zerobot.packagemanager.actors.package_manager.package_start(args).then((resp) => {
			if(resp.ok) {
				lastError = null;
				updatePackages()
       		} else {
				lastError = "Couldn't start package " + name;
			}
		})
	}

	function packageDelete(name) {
		let args = {name: name}
		packageGedisClient.zerobot.packagemanager.actors.package_manager.package_delete(args).then((resp) => {
			if(resp.ok) {
				lastError = null;
				updatePackages()
       		} else {
				lastError = "Couldn't delete package " + name;
			}
		})
	}
</script>

<svelte:head>
	<title>3bot Package Manager</title>
</svelte:head>

<h2>3Bot Package Manager</h2><br><br>

<form>
	{#if lastError != null }
		<div class="alert alert-danger" role="alert">{lastError}</div>
	{/if}
	<div class="form-row align-items-center">
		<div class="col-auto">
			<select bind:value="{method}" class="custom-select mr-sm-3" id="inlineFormCustomSelect">
				<option value="path" selected>path</option>
				<option value="git_url">giturl</option>
			</select>
		</div>
		<div class="col-6">
			<div class="input-group mb-2">
				<input type="text" bind:value="{newPackagePath}" class="form-control" id="inlineFormInputGroup">
			</div>
		</div>
		<div class="col-auto">
			<button type="button" class="btn btn-primary mb-2" on:click={()=>packageAdd()}>Add package</button>
		</div>
	</div>
</form>
<table class="table" style="margin-top:20px;">
  <caption>Packages</caption>
  <thead>
    <tr>
      <th scope="col">Name</th>
      <th scope="col">Status</th>
      <th scope="col">Path</th>
      <th scope="col">Actions</th>
    </tr>
  </thead>
  <tbody>
	{#each packages as pkg}
    <tr>
      <th scope="row">{pkg.name}</th>
      <td>{pkgStatus[pkg.status].name}</td>
      <td>{pkg.path}</td>
      <td>
	  	{#if pkgStatus[pkg.status].actions.includes('start') }
	  		<button type="button" class="btn btn-success btn-sm" on:click={()=>packageStart(pkg.name)}>Start</button>
		{/if}

		{#if pkgStatus[pkg.status].actions.includes('stop') }
	  		<button type="button" class="btn btn-danger btn-sm" on:click={()=>packageStop(pkg.name)}>Stop</button>
		{/if}

		{#if pkgStatus[pkg.status].actions.includes('enable') }
	  		<button type="button" class="btn btn-primary btn-sm" on:click={()=>packageEnable(pkg.name)}>Enable</button>
		{/if}

		{#if pkgStatus[pkg.status].actions.includes('disable') }
	  		<button type="button" class="btn btn-light btn-sm" on:click={()=>packageDisable(pkg.name)}>Disable</button>
		{/if}
		{#if pkgStatus[pkg.status].actions.includes('delete') }
	  		<button type="button" class="btn btn-dark btn-sm" on:click={()=>packageDelete(pkg.name)}>Delete</button>
		{/if}
	  </td>
    </tr>
	{/each}
  </tbody>
</table>
