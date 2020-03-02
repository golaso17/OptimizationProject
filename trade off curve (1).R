library(ggplot2)
df<- data.frame(flow=c(),
                 fairness_metric=c())

ggplot(data=df, aes(x=flow, y=fairness_metric, group=1)) +
  geom_line()+
  geom_point()
# Change the line type
ggplot(data=df, aes(x=flow, y=fairness_metric, group=1)) +
  geom_line(linetype = "dashed")+
  geom_point()
# Change the color
ggplot(data=df, aes(x=flow, y=fairness_metric, group=1)) +
  geom_line(color="red")+
  geom_point() 