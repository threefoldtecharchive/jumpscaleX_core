<script>
  import { restore, mutate } from 'svelte-apollo';
  import { client } from './apollo';
  import gql from 'graphql-tag';

  const AUTHOR_LIST = gql`
    query {
      author {
        name
      }
    }
  `;
  const ADD_AUTHOR = gql`
    mutation($name: String!) {
      createAuthor(name: $name) {
        affected_rows
      }
    }
  `;
  let name = '';
  export let authorCache;
  
  async function addAuthor(e) {
    e.preventDefault();
    try {
      await mutate(client, {
        mutation: gql`
            mutation{
                createAuthor(name: "${ name }") {
                    affectedRows
                }
            }
        `
      });
      alert("Added successfully");
      const finalData = authorCache.data.author;
      finalData.push({name, '__typename': 'author'});
      restore(client, AUTHOR_LIST, {author: finalData});
      // clear input
      name = '';
    } catch(error) {
      console.error(error);
    }
  }
</script>

<form on:submit={addAuthor}>
  <label for="author">Author</label>
  <input type="text" id="author-name" bind:value={name} />
  <button type="submit">Add Author</button>
</form>