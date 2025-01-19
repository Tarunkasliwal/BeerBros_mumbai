company_info,
                    sentiment_summary
                )
                ad_content = analyzer.ollama_generator.generate_ad(prompt)
                st.session_state['ad_content'] = ad_content
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Insights", "Sentiment Analysis", "Damage Control", "AI Ad Suggestions", "Raw Data"
    ])
    
    if 'data' in st.session_state:
        df = st.session_state['data']
        
        with tab1:
            st.header("Insights")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Average Sentiment", f"{df['sentiment_score'].mean():.2f}")
            with col2:
                st.metric("Positive Tweets", len(df[df['sentiment_category'] == 'positive']))
            with col3:
                st.metric("Negative Tweets", len(df[df['sentiment_category'] == 'negative']))
                
            st.subheader("Engagement Overview")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Retweets", df['retweet_count'].sum())
            with col2:
                st.metric("Total Likes", df['like_count'].sum())
            with col3:
                st.metric("Total Replies", df['reply_count'].sum())
        
        with tab2:
            st.header("Sentiment Analysis")
            fig = px.histogram(df, x='sentiment_score', nbins=20,
                             title='Sentiment Distribution')
            st.plotly_chart(fig)
            
            gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = df['sentiment_score'].mean(),
                title = {'text': "Average Sentiment"},
                gauge = {'axis': {'range': [-1, 1]}}
            ))
            st.plotly_chart(gauge)
            
            df['created_at'] = pd.to_datetime(df['created_at'])
            fig = px.line(df.sort_values('created_at'), 
                         x='created_at', 
                         y='sentiment_score',
                         title='Sentiment Trend Over Time')
            st.plotly_chart(fig)
        
        with tab3:
            st.header("Damage Control")
            negative_tweets = df[df['sentiment_category'] == 'negative']
            
            for _, tweet in negative_tweets.iterrows():
                with st.expander(f"🚨 Tweet from {tweet['author_id']}"):
                    st.write(tweet['text'])
                    st.write(f"Sentiment Score: {tweet['sentiment_score']:.2f}")
                    st.write(f"Engagement: {tweet['retweet_count']} RTs, {tweet['like_count']} Likes")
                    
                    st.write("Suggested Actions:")
                    for suggestion in analyzer.generate_damage_control_suggestions(tweet):
                        st.write(f"- {suggestion}")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.button("Respond", key=f"respond_{tweet['id']}")
                    with col2:
                        st.button("Monitor", key=f"monitor_{tweet['id']}")
                    with col3:
                        st.button("Report", key=f"report_{tweet['id']}")
        
        with tab4:
            st.header("AI-Generated Ad Suggestions")
            
            if 'ad_content' in st.session_state:
                st.subheader("🎯 Generated Ad Content")
                st.write(st.session_state['ad_content'])
                
                st.subheader("📊 Data-Driven Ad Ideas")
                traditional_ads = analyzer.ad_generator.generate_ad_ideas(df)
                
                for i, ad in enumerate(traditional_ads, 1):
                    with st.expander(f"Ad Idea {i}: {ad['type'].replace('_', ' ').title()}"):
                        st.write(f"**Content:** {ad['content']}")
                        st.write(f"**Target Emotion:** {ad['target_emotion']}")
                        st.write(f"**Trending Topic:** #{ad['trending_topic']}")
                        
                        creative_generator = CreativeAssetGenerator()
                        svg_content = creative_generator.generate_ad_visual(ad)
                        st.write("**Visual Preview:**")
                        st.markdown(f'<div style="background: white; padding: 10px;">{svg_content}</div>', 
                                  unsafe_allow_html=True)
        
        with tab5:
            st.header("Raw Data")
            st.dataframe(df)
            
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="twitter_analysis.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()