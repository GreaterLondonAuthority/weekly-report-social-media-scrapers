// This script is intended to run in the browser's developer tools console.
// This is temporary solution before an automated solution is developed.

function downloadCSV(data, filename) {
	const csvContent = [
		[
			'Post #',
			'Publish Time',
			'Post Content',
			'Likes',
			'Replies',
			'Reposts',
			'Shares',
		], // Header
		...data.map((row, index) => [
			index + 1,
			row.publishTime,
			`"${row.postText.replace(/"/g, '""')}"`, // Escape double quotes in post content
			row.likes,
			row.replies,
			row.reposts,
			row.shares,
		]),
	]
		.map((e) => e.join(',')) // Join each row with commas
		.join('\n'); // Join rows with newlines

	const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
	const link = document.createElement('a');
	const url = URL.createObjectURL(blob);
	link.setAttribute('href', url);
	link.setAttribute('download', filename);
	link.style.visibility = 'hidden';
	document.body.appendChild(link);
	link.click();
	document.body.removeChild(link);
}
 
async function captureVisiblePostsAndEngagement() {
	const capturedData = [];

	// Capture the visible posts on the page using the provided selector for posts
	const posts = document.querySelectorAll('.x78zum5.xdt5ytf'); // Post selector

	posts.forEach((post) => {
		// Function to get the publish time
		function getPublishTime() {
			// Try the first selector (for relative times like "1h", "2d", etc.)
			let publishTimeElement = post.querySelector(
				'.html-span.xdj266r.x11i5rnm.xat24cr.x1mh8g0r.xexx8yu.x4uap5.x18d9i69.xkhd6sd.x1hl2dhg.x16tdsg8.x1vvkbs'
			);
			if (publishTimeElement) {
				return publishTimeElement.innerText.trim();
			}

			// Try the second selector (for absolute dates like "10/01/2024")
			publishTimeElement = post.querySelector(
				'.x1rg5ohu.xnei2rj.x2b8uid.xuxw1ft'
			);
			if (publishTimeElement) {
				return publishTimeElement.innerText.trim();
			}

			// Default to 'N/A' if neither selector matches
			return 'N/A';
		}

		const publishTime = getPublishTime();
		// Get the post text using the provided selector for post text
		const postTextElement = post.querySelector(
			'.x1a6qonq.x6ikm8r.x10wlt62.xj0a0fe.x126k92a.x6prxxf.x7r5mf7'
		);
		const postText = postTextElement ? postTextElement.innerText.trim() : '';

		// Function to get engagement numbers based on the inner span selector
		function getEngagementText(iconLabel) {
			const parentElement = post.querySelector(
				`svg[aria-label="${iconLabel}"]`
			);
			if (parentElement) {
				// Find the span with engagement number after the parent element
				const engagementSpan = parentElement
					.closest('div')
					.querySelector('span.x17qophe.x10l6tqk.x13vifvy');
				return engagementSpan ? engagementSpan.innerText.trim() : '0';
			}
			return '0';
		}

		// Get the likes, replies, reposts, and shares
		const likes = getEngagementText('Like');
		const replies = getEngagementText('Reply');
		const reposts = getEngagementText('Repost');
		const shares = getEngagementText('Share');

		// Add the captured post and engagement data to the results array
		const postData = { publishTime, postText, likes, replies, reposts, shares };
		if (!capturedData.some((data) => data.postText === postText)) {
			capturedData.push(postData);
		}
	});

	// Log the results in a table format (optional)
	console.table(
		capturedData.map((data, index) => ({
			'Post #': index + 1,
			'Publish Time': data.publishTime,
			'Post Content': data.postText,
			Likes: data.likes,
			Replies: data.replies,
			Reposts: data.reposts,
			Shares: data.shares,
		}))
	);

	// Call the CSV download function
	downloadCSV(capturedData, 'posts-engagement.csv');
}

// Run the function to capture visible posts and download as CSV
captureVisiblePostsAndEngagement();
